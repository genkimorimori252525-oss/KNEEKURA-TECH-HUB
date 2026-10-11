#!/usr/bin/env python3
"""Fail-closed receipt validation for exact-game Warfare Wings AI control traces.

This checks the observed *result* of real vehicle commands, not source-physics parity,
combat victory or historical accuracy. The receipt may only be marked MEASURED if
the Forge GameTest actually emitted the complete runtime traces.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

EXPECTED = {
    "a6m-steered-interception": "warfare_wings:a6m",
    "p47n-steered-interception": "warfare_wings:p47n",
    "il2-ground-approach-no-fire": "warfare_wings:il2",
    "b17-level-bomb-guidance-only": "warfare_wings:b17",
    "g4m-torpedo-guidance-only": "warfare_wings:g4m",
}
SCHEMA = "ww.physics.forge-tactical-pilot.v1"
SOURCE = "minecraft_runtime_ia_next_tick_injection"
SAMPLES = 181  # 0 initial + exactly 180 real entity updates
COLUMNS = [
    "schema_version", "source", "scenario_id", "aircraft_id", "sim_tick",
    "game_time", "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
    "yaw_deg", "pitch_deg", "engine_target", "engine_power", "smooth_x",
    "smooth_z", "command_x", "command_z", "command_throttle", "maneuver",
    "reason", "world_safety_reason", "terrain_clearance_blocks",
]
NUMERIC = [
    "pos_x", "pos_y", "pos_z", "vel_x", "vel_y", "vel_z",
    "yaw_deg", "pitch_deg", "engine_target", "engine_power", "smooth_x",
    "smooth_z", "command_x", "command_z", "command_throttle",
    "terrain_clearance_blocks",
]


class ReceiptError(ValueError):
    pass


def checked(value: str, key: str, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ReceiptError(f"{label}: nonnumeric {key}") from exc
    if not math.isfinite(result):
        raise ReceiptError(f"{label}: nonfinite {key}")
    return result


def load_one(path: Path, scenario: str, aircraft: str) -> dict:
    label = f"{scenario} ({path.name})"
    if not path.is_file():
        raise ReceiptError(f"{label}: trace missing")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ReceiptError(f"{label}: invalid column ordering/schema")
        rows = list(reader)
    if len(rows) != SAMPLES:
        raise ReceiptError(f"{label}: expected {SAMPLES} data samples, got {len(rows)}")

    parsed = []
    previous_game_time = None
    for index, row in enumerate(rows):
        if any(k is None or v is None for k, v in row.items()):
            raise ReceiptError(f"{label}: ragged CSV row {index}")
        if (row["schema_version"], row["source"], row["scenario_id"], row["aircraft_id"]) != (
            SCHEMA, SOURCE, scenario, aircraft
        ):
            raise ReceiptError(f"{label}: identity/provenance mismatch sample {index}")
        if not row["maneuver"] or not row["reason"] or not row["world_safety_reason"]:
            raise ReceiptError(f"{label}: missing control decision at {index}")
        try:
            tick = int(row["sim_tick"])
            game_time = int(row["game_time"])
        except ValueError as exc:
            raise ReceiptError(f"{label}: invalid tick number at {index}") from exc
        if tick != index:
            raise ReceiptError(f"{label}: missing/duplicate/out-of-order tick {index} ({tick})")
        if previous_game_time is not None and game_time != previous_game_time + 1:
            raise ReceiptError(f"{label}: nonconsecutive game tick {index}")
        previous_game_time = game_time
        nums = {key: checked(row[key], key, label) for key in NUMERIC}
        for key in ("command_x", "command_z", "smooth_x", "smooth_z"):
            if abs(nums[key]) > 1.00001:
                raise ReceiptError(f"{label}: out-of-range {key} at {index}")
        for key in ("engine_target", "command_throttle"):
            if not 0.0 <= nums[key] <= 1.00001:
                raise ReceiptError(f"{label}: out-of-range {key} at {index}")
        if nums["engine_power"] < -0.00001:
            raise ReceiptError(f"{label}: invalid engine power at {index}")
        parsed.append(nums)

    # The live adapter runs at ServerTick.END. IA first applies update(0) to
    # previous smooth, and then the bridge corrects it with +0.1*current raw.
    # This recurrence is independently sourced to pinned IA 1.3.3 code.
    for index in range(1, SAMPLES):
        old, new = parsed[index - 1], parsed[index]
        for axis in ("x", "z"):
            predicted = 0.9 * old[f"smooth_{axis}"] + 0.1 * new[f"command_{axis}"]
            if abs(predicted - new[f"smooth_{axis}"]) > 0.0005:
                raise ReceiptError(f"{label}: actual IA input smoothing failed at tick {index}, {axis}")

    lateral = 0
    yaw_travel = 0.0
    first_command = None
    first_yaw_response = None
    for index in range(1, SAMPLES):
        now, previous = parsed[index], parsed[index - 1]
        if abs(now["command_x"]) > 0.001:
            lateral += 1
            if first_command is None:
                first_command = index
        yaw = (now["yaw_deg"] - previous["yaw_deg"] + 540) % 360 - 180
        yaw_travel += abs(yaw)
        if abs(yaw) > 0.005 and first_yaw_response is None:
            first_yaw_response = index

    start, end = parsed[0], parsed[-1]
    displacement = math.sqrt(sum(
        (end[f"pos_{axis}"] - start[f"pos_{axis}"]) ** 2 for axis in "xyz"
    ))
    if lateral < 10 or yaw_travel < 2 or displacement < 8:
        raise ReceiptError(
            f"{label}: insufficient real flight motion xTicks={lateral}, "
            f"yawTravel={yaw_travel:.3f}, displacement={displacement:.3f}"
        )
    if first_command is None or first_yaw_response is None or first_yaw_response <= first_command:
        raise ReceiptError(f"{label}: first yaw response did not follow first steering command")

    return {
        "scenario": scenario,
        "aircraft_id": aircraft,
        "source": SOURCE,
        "samples": SAMPLES,
        "nonzero_lateral_ticks": lateral,
        "yaw_travel_deg": round(yaw_travel, 6),
        "displacement_blocks": round(displacement, 6),
        "first_command_tick": first_command,
        "first_yaw_response_tick": first_yaw_response,
        "input_smoothing": "IA_1.3.3_END_CORRECTION_CHECKED",
        "evidence": "MEASURED_RUNTIME_TRACE_EXISTENCE_AND_CONTROL_ONLY",
    }


def verify(directory: Path) -> dict:
    cases = [load_one(directory / f"{case}-forge-controls.csv", case, aircraft)
             for case, aircraft in EXPECTED.items()]
    return {
        "schema_version": "ww.physics.tactical-runtime-receipt.v1",
        "conclusion": "FIVE_RUNTIME_CONTROL_TRACES_VERIFIED",
        "physics_parity": "NOT_DETERMINED_BY_RECEIPTS",
        "weapons_and_combat": "NOT_TESTED_BY_RECEIPTS",
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path, help="actual Forge GameTest ww-physics-traces directory")
    parser.add_argument("--summary", type=Path, help="write verified JSON summary (only upon PASS)")
    args = parser.parse_args()
    summary = verify(args.trace_dir)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for item in summary["cases"]:
        print("TACTICAL_REAL_TRACE_RECEIPT_OK", item["scenario"],
              "ticks=180", f"yaw={item['yaw_travel_deg']}",
              f"moved={item['displacement_blocks']}")
    print("FIVE_RUNTIME_CONTROL_TRACES_VERIFIED; source parity and combat effectiveness NOT_DETERMINED")


if __name__ == "__main__":
    main()

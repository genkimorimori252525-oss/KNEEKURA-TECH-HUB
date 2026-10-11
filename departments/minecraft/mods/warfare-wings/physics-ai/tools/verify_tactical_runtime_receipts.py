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

ATLAS_CSV = Path(__file__).resolve().parent.parent / "data/base-aircraft-anchor-v1.csv"
INPUT_SMOOTH_FACTOR = 0.1  # Pinned IA InterpolatedFloat(10)
EXPECTED_ANCHOR_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"

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


def source_airframe_retention(atlas_csv: Path = ATLAS_CSV) -> dict[str, float]:
    """Use the 24 exact-ANCHOR model coefficients, never fit measured traces."""
    if not atlas_csv.is_file():
        raise ReceiptError(f"Missing source Atlas: {atlas_csv}")
    with atlas_csv.open(encoding="utf-8", newline="") as handle:
        entries = list(csv.DictReader(handle))
    if len(entries) != 24:
        raise ReceiptError(f"Expected exactly 24 researched airframes, got {len(entries)}")
    values = {}
    for row in entries:
        ident = row["aircraft_id"]
        if row["anchor_sha256"] != EXPECTED_ANCHOR_SHA256:
            raise ReceiptError(f"Wrong source binary provenance for {ident}")
        friction = checked(row["effective_friction"], "effective_friction", ident)
        rotation = checked(row["effective_rotationDecay"], "effective_rotationDecay", ident)
        if not 0 <= friction < 1 or not 0 < rotation <= 1 or ident in values:
            raise ReceiptError(f"Invalid or duplicate source rotation model: {ident}")
        values[ident] = (1.0 - INPUT_SMOOTH_FACTOR) * (1.0 - friction) * rotation
    return values


def checked(value: str, key: str, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ReceiptError(f"{label}: nonnumeric {key}") from exc
    if not math.isfinite(result):
        raise ReceiptError(f"{label}: nonfinite {key}")
    return result


def load_one(path: Path, scenario: str, aircraft: str,
             retention: float | None = None, *,
             expected_samples: int = SAMPLES,
             min_lateral_ticks: int = 10,
             min_yaw_deg: float = 2.0,
             min_displacement: float = 8.0) -> dict:
    label = f"{scenario} ({path.name})"
    if retention is None:
        # Tests can call load_one directly and still get the exact model.
        atlas = source_airframe_retention()
        retention = atlas.get(aircraft)
    if retention is None or not math.isfinite(retention):
        raise ReceiptError(f"{label}: aircraft absent from exact 24-type source Atlas")
    if not path.is_file():
        raise ReceiptError(f"{label}: trace missing")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ReceiptError(f"{label}: invalid column ordering/schema")
        rows = list(reader)
    if (expected_samples < 2 or min_lateral_ticks < 1
            or min_yaw_deg <= 0 or min_displacement <= 0):
        raise ReceiptError(f"{label}: invalid fixed acceptance floor")
    if len(rows) != expected_samples:
        raise ReceiptError(f"{label}: expected {expected_samples} data samples, got {len(rows)}")

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

    # The live adapter runs at ServerTick.END. IA first applies the *aircraft's*
    # rotation retention (airborne friction and rotation decay), then input
    # interpolation update(0), before adding 0.1 * the new AI command.
    # SOURCE: Ia133Microkernel.tick() smoothXForController=prior *
    # ((1-model.friction)*model.rotationDecay), then smooth=.9*...+.1*raw.
    # Exact 24-type coefficients come from the owner's pinned ANCHOR CSV;
    # for A6M/P47N/B17 etc retention = .9 * .985 * .97 = .859905.
    # A simple .9 multiplier would reject REAL correct aircraft motion.
    for index in range(1, expected_samples):
        old, new = parsed[index - 1], parsed[index]
        for axis in ("x", "z"):
            predicted = retention * old[f"smooth_{axis}"] + INPUT_SMOOTH_FACTOR * new[f"command_{axis}"]
            if abs(predicted - new[f"smooth_{axis}"]) > 0.0005:
                raise ReceiptError(f"{label}: actual IA input smoothing failed at tick {index}, {axis}")

    lateral = 0
    yaw_travel = 0.0
    first_command = None
    first_yaw_response = None
    yaw_deltas = []
    for index in range(1, expected_samples):
        now, previous = parsed[index], parsed[index - 1]
        if abs(now["command_x"]) > 0.001:
            lateral += 1
            if first_command is None:
                first_command = index
        yaw = (now["yaw_deg"] - previous["yaw_deg"] + 540) % 360 - 180
        yaw_deltas.append(abs(yaw))
        yaw_travel += abs(yaw)
        if abs(yaw) > 0.005 and first_yaw_response is None:
            first_yaw_response = index

    start, end = parsed[0], parsed[-1]
    displacement = math.sqrt(sum(
        (end[f"pos_{axis}"] - start[f"pos_{axis}"]) ** 2 for axis in "xyz"
    ))
    if lateral < min_lateral_ticks or yaw_travel < min_yaw_deg or displacement < min_displacement:
        raise ReceiptError(
            f"{label}: insufficient real flight motion xTicks={lateral}, "
            f"yawTravel={yaw_travel:.3f}, displacement={displacement:.3f}"
        )
    # The physics engine may already be yawing on sample 1 *before* the first
    # server-END AI command. A pre-existing yaw change cannot prove or disprove
    # the command's one-tick delay; requiring its absence would reject genuine
    # aircraft dynamics. Require meaningful continued yaw AFTER the first
    # command instead; the independently checked smoother recurrence proves
    # control injection, but only a neutral-control A/B trace can establish
    # full yaw causality.
    if first_command is None:
        raise ReceiptError(f"{label}: no usable lateral command")
    post_command_yaw_travel = sum(yaw_deltas[first_command:])
    if post_command_yaw_travel < min_yaw_deg:
        raise ReceiptError(f"{label}: no sustained post-command yaw response")

    return {
        "scenario": scenario,
        "aircraft_id": aircraft,
        "source": SOURCE,
        "samples": expected_samples,
        "nonzero_lateral_ticks": lateral,
        "yaw_travel_deg": round(yaw_travel, 6),
        "post_command_yaw_travel_deg": round(post_command_yaw_travel, 6),
        "displacement_blocks": round(displacement, 6),
        "first_command_tick": first_command,
        "first_yaw_response_tick": first_yaw_response,
        "input_smoothing": "IA_1.3.3_END_CORRECTION_CHECKED",
        "source_airframe_smooth_retention": round(retention, 9),
        "evidence": "MEASURED_RUNTIME_TRACE_CONTROL_AND_MOTION_CAUSALITY_UNPROVEN",
    }


def verify(directory: Path, atlas_csv: Path = ATLAS_CSV) -> dict:
    retention = source_airframe_retention(atlas_csv)
    cases = [load_one(directory / f"{case}-forge-controls.csv", case, aircraft,
                      retention.get(aircraft))
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
    parser.add_argument("--atlas", type=Path, default=ATLAS_CSV,
                        help="24-aircraft exact ANCHOR provenance CSV; no runtime coefficient fitting")
    parser.add_argument("--summary", type=Path, help="write verified JSON summary (only upon PASS)")
    args = parser.parse_args()
    summary = verify(args.trace_dir, args.atlas)
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

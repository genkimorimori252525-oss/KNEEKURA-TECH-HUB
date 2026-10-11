#!/usr/bin/env python3
"""Synthetic negative fixtures for the Forge receipt checker; no actual game claims."""

import csv
from pathlib import Path
import tempfile

from verify_tactical_runtime_receipts import (
    COLUMNS, EXPECTED, ReceiptError, SCHEMA, SOURCE, verify,
    source_airframe_retention, INPUT_SMOOTH_FACTOR,
)


def fixture(scenario: str, aircraft: str) -> list[dict[str, str]]:
    rows = []
    smooth = 0.0
    retention = source_airframe_retention()[aircraft]
    for tick in range(181):
        control = .5 if 1 <= tick <= 40 else 0.0
        if tick:
            smooth = retention * smooth + INPUT_SMOOTH_FACTOR * control
        row = dict.fromkeys(COLUMNS, "")
        row.update({
            "schema_version": SCHEMA, "source": SOURCE, "scenario_id": scenario,
            "aircraft_id": aircraft, "sim_tick": str(tick),
            "game_time": str(1000 + tick),
            "pos_x": "0", "pos_y": "200", "pos_z": str(tick * .14),
            "vel_x": "0", "vel_y": "0", "vel_z": ".14",
            "yaw_deg": str(max(0, tick - 1) * .03), "pitch_deg": "0",
            "engine_target": "1", "engine_power": ".8",
            "smooth_x": str(smooth), "smooth_z": "0",
            "command_x": str(control), "command_z": "0",
            "command_throttle": "1", "maneuver": "INTERCEPT",
            "reason": "SYNTHETIC_TEST_ONLY",
            "world_safety_reason": "CLEAR", "terrain_clearance_blocks": "200",
        })
        rows.append(row)
    return rows


def write(directory: Path, scenario: str, rows: list[dict[str, str]]) -> None:
    with (directory / f"{scenario}-forge-controls.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def expect_failure(directory: Path, fragment: str) -> None:
    try:
        verify(directory)
    except ReceiptError as error:
        if fragment not in str(error):
            raise AssertionError(f"wrong rejection: {error!s}, expected {fragment}") from error
    else:
        raise AssertionError(f"tampered trace unexpectedly passed: {fragment}")


def main() -> None:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="ww-forge-receipt-fixtures-") as tmp:
        directory = Path(tmp)
        data = {scenario: fixture(scenario, aircraft) for scenario, aircraft in EXPECTED.items()}
        for scenario, rows in data.items():
            write(directory, scenario, rows)
        normal = verify(directory)
        assert len(normal["cases"]) == 5
        assert all(x["samples"] == 181 for x in normal["cases"])
        checks += 2

        name = next(iter(EXPECTED))
        normal_rows = data[name]
        mutations = [
            (1, "sim_tick", "99", "missing/duplicate/out-of-order tick"),
            (5, "game_time", "1007", "nonconsecutive game tick"),
            (9, "aircraft_id", "warfare_wings:wrong", "identity/provenance mismatch"),
            (3, "schema_version", "unknown", "identity/provenance mismatch"),
            (8, "command_x", "2.0", "out-of-range"),
            (8, "smooth_x", "0", "input smoothing failed"),
            (8, "vel_z", "NaN", "nonfinite"),
            (8, "command_throttle", "-1", "out-of-range"),
            (8, "source", "source_microkernel", "identity/provenance mismatch"),
        ]
        for index, field, value, expected in mutations:
            mutated = [dict(x) for x in normal_rows]
            mutated[index][field] = value
            write(directory, name, mutated)
            expect_failure(directory, expected)
            checks += 1
            write(directory, name, normal_rows)

        write(directory, name, normal_rows[:-1])
        expect_failure(directory, "expected 181 data samples")
        checks += 1
        write(directory, name, normal_rows)

        no_motion = [dict(x) for x in normal_rows]
        for row in no_motion:
            row["pos_z"] = "0"
        write(directory, name, no_motion)
        expect_failure(directory, "insufficient real flight motion")
        checks += 1
        write(directory, name, normal_rows)

        no_response = [dict(x) for x in normal_rows]
        for row in no_response:
            row["yaw_deg"] = "0"
        write(directory, name, no_response)
        expect_failure(directory, "insufficient real flight motion")
        checks += 1
        write(directory, name, normal_rows)

        # Real IA can yaw passively before the first server-END pilot command:
        # this must not cause a false failure in the receipt checker.
        passive_yaw = [dict(x) for x in normal_rows]
        for index in range(1, len(passive_yaw)):
            passive_yaw[index]["yaw_deg"] = str(float(passive_yaw[index]["yaw_deg"]) + 0.03)
        write(directory, name, passive_yaw)
        assert len(verify(directory)["cases"]) == 5
        checks += 1
        write(directory, name, normal_rows)

        # A one-time passive heading jump is NOT sustained steering evidence.
        transient = [dict(x) for x in normal_rows]
        for index, row in enumerate(transient):
            row["yaw_deg"] = "0" if index == 0 else "5"
        write(directory, name, transient)
        expect_failure(directory, "no sustained post-command yaw response")
        checks += 1
        write(directory, name, normal_rows)

        (directory / f"{name}-forge-controls.csv").unlink()
        expect_failure(directory, "trace missing")
        checks += 1
    print(f"TacticalRuntimeReceiptSelfTest passed: {checks} independent synthetic checks;"
          " exact Minecraft runtime NOT_RUN")


if __name__ == "__main__":
    main()

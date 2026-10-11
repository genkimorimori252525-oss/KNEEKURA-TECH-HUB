#!/usr/bin/env python3
"""Exact-artifact 24-plane sequential Forge smoke acceptance.

This tests individual actual airplane entities receiving pilot controls and
moving through real Minecraft. It is not 24-plane concurrent combat, nor a
calibrated parity ranking; strict decisions use the source-proven 24-airframe
provenance and smoothing law rather than fitted pass/fail metrics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_tactical_runtime_receipts import (
    ATLAS_CSV, ReceiptError, load_one, source_airframe_retention,
)


def verify(directory: Path, atlas_csv: Path = ATLAS_CSV) -> dict:
    roster = source_airframe_retention(atlas_csv)
    if len(roster) != 24:
        raise ReceiptError("24 actual aircraft required")
    results = []
    for aircraft in sorted(roster):
        scenario = "roster-" + aircraft.split(":", 1)[1]
        path = directory / f"{scenario}-forge-controls.csv"
        results.append(load_one(
            path, scenario, aircraft, roster[aircraft],
            expected_samples=41, min_lateral_ticks=3,
            min_yaw_deg=0.25, min_displacement=4,
        ))
    return {
        "schema_version": "ww.physics.24-aircraft-runtime-smoke.v1",
        "status": "ALL_24_SEQUENTIAL_RUNTIME_SMOKES_VERIFIED",
        "plane_count": len(results),
        "min_samples_per_plane": 41,
        "full_physics_parity": "NOT_ESTABLISHED",
        "simultaneous_dogfight": "NOT_TESTED",
        "weapons": "NOT_TESTED",
        "aircraft": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    parser.add_argument("--atlas", type=Path, default=ATLAS_CSV)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    result = verify(args.trace_dir, args.atlas)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for case in result["aircraft"]:
        print("REAL_ROSTER_SMOKE_OK", case["aircraft_id"], "ticks=40",
              "moved=", case["displacement_blocks"],
              "yaw=", case["yaw_travel_deg"])
    print("ALL_24_SEQUENTIAL_RUNTIME_SMOKES_VERIFIED; "
          "physics parity and simultaneous combat NOT_ESTABLISHED")


if __name__ == "__main__":
    main()

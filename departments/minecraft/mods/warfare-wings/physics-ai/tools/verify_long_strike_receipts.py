#!/usr/bin/env python3
"""Strict independent acceptance of synchronized real IL2/B17 ingress/egress/RTB.

No ordnance is released. Passing approach/egress/return geometry is NEVER a
hit, kill, bomb/rocket release, target destruction or successful landing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE, load_one

SAMPLES = 841
PHASES = ("STRIKE_INGRESS", "STRIKE_EGRESS", "RETURNING")
AIRCRAFT = {"il2": "warfare_wings:il2", "b17": "warfare_wings:b17"}


def verify(trace_dir: Path) -> dict:
    summaries = []
    actors = {}
    failures = []
    for ident, aircraft_id in AIRCRAFT.items():
        scenario = f"operational-strike-{ident}"
        path = trace_dir / f"{scenario}-forge-controls.csv"
        # In addition to phase acceptance, verify exact IA input smoothing,
        # finite controls, and enough real motion, using unchanged Atlas data.
        control = load_one(path, scenario, aircraft_id, expected_samples=SAMPLES,
                           min_lateral_ticks=10, min_yaw_deg=2, min_displacement=60)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != COLUMNS:
                raise ValueError(f"{scenario}: wrong original runtime trace schema")
            rows = list(reader)
        if len(rows) != SAMPLES:
            raise ValueError(f"{scenario}: incomplete 841 real physics samples")
        phase_labels = []
        positions = []
        clocks = []
        for index, row in enumerate(rows):
            if (row["schema_version"], row["source"], row["scenario_id"], row["aircraft_id"]) != (
                SCHEMA, SOURCE, scenario, aircraft_id):
                raise ValueError(f"{scenario}: incorrect original runtime provenance at tick {index}")
            match = re.search(r"(?:^|\|)phase=(STRIKE_INGRESS|STRIKE_EGRESS|RETURNING|TRANSIT)(?:\||$)", row["reason"])
            if match is None:
                if index == 0 and row["reason"] == "INITIAL" and row["maneuver"] == "INITIAL":
                    phase_labels.append("TRANSIT")
                    positions.append(tuple(float(row[f"pos_{axis}"]) for axis in "xyz"))
                    clocks.append(int(row["game_time"]))
                    continue
                raise ValueError(f"{scenario}: missing actual server mission-phase receipt at {index}")
            phase_labels.append(match.group(1))
            positions.append(tuple(float(row[f"pos_{axis}"]) for axis in "xyz"))
            clocks.append(int(row["game_time"]))
        if any(not all(math.isfinite(v) for v in pos) for pos in positions):
            raise ValueError(f"{scenario}: nonfinite flight position")
        counts = {phase: phase_labels.count(phase) for phase in PHASES}
        phase_ticks = [next((i for i, p in enumerate(phase_labels) if p == phase), -1)
                       for phase in PHASES]
        if not all(x >= 0 for x in phase_ticks) or phase_ticks != sorted(phase_ticks):
            failures.append(f"PHASES_INCOMPLETE_OR_OUT_OF_ORDER:{ident}:{phase_ticks}")
        if counts["STRIKE_INGRESS"] < 50 or counts["STRIKE_EGRESS"] < 12 or counts["RETURNING"] < 50:
            failures.append(f"PHASE_DURATION_FAILED:{ident}:{counts}")
        if phase_ticks[1] >= 0:
            first = positions[0]
            objective = (first[0], first[1], first[2] + 185)
            min_dist = min(math.dist(p, objective) for p in positions[:phase_ticks[1]+1])
        else:
            min_dist = math.inf
        if min_dist >= 75:
            failures.append(f"REAL_TARGET_INGRESS_NOT_REACHED:{ident}:min={min_dist:.3f}")
        if phase_ticks[2] >= 0:
            home = (positions[0][0], positions[0][1], positions[0][2] - 130)
            start_home = math.dist(positions[phase_ticks[2]], home)
            min_home = min(math.dist(pos, home) for pos in positions[phase_ticks[2]:])
        else:
            start_home = math.inf
            min_home = math.inf
        if start_home - min_home < 4:
            failures.append(f"REAL_HOME_DISTANCE_NOT_REDUCED:{ident}:delta={start_home-min_home:.3f}")
        summaries.append({"aircraft": aircraft_id, "samples": len(rows),
                          "phase_ticks": dict(zip(PHASES, phase_ticks)),
                          "phase_counts": counts,
                          "closest_target_blocks": round(min_dist, 6),
                          "home_distance_reduction_blocks": round(start_home - min_home, 6),
                          "displacement_blocks": control["displacement_blocks"],
                          "yaw_travel_deg": control["yaw_travel_deg"]})
        actors[ident] = {"positions": positions, "clocks": clocks}
    if actors["il2"]["clocks"] != actors["b17"]["clocks"]:
        raise ValueError("IL2 and B17 were not physically measured on the same Minecraft ticks")
    nearest = min(math.dist(a, b) for a, b in zip(actors["il2"]["positions"], actors["b17"]["positions"]))
    if nearest < 6:
        failures.append(f"STRIKE_BODY_SEPARATION_LT6:min={nearest:.6f}")
    return {"schema_version": "ww.physics.real-strike-rtb-receipt.v1",
            "evidence": "ACTUAL_MINECRAFT_SERVER_ENTITY_TICKS_NO_ORDNANCE",
            "scenario": "operational-long-strike-rtb",
            "nearest_aircraft_blocks": round(nearest, 6),
            "units": summaries, "failed_operational_gates": failures,
            "conclusion": "FAILED" if failures else "NO_WEAPON_GEOMETRIC_APPROACH_EGRESS_RTB_PASSED"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_dir", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.trace_dir)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"REAL_LONG_STRIKE_RECEIPT_FAILED: {exc}") from None
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    if result["failed_operational_gates"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

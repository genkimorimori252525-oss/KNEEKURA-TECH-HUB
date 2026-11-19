#!/usr/bin/env python3
"""Independent observed-threat selection audit of original-Forge B17 receipts.

Only exact original five-aircraft GameTest CSVs can supply these observations.
This verifies that an explicitly assigned protected aircraft/escort pilot
actually selected among FOV/LOS-visible hostiles, never that it protected the
95-block radius, fired a weapon, hit anything or won a battle.
"""

from __future__ import annotations

import argparse
import csv
import json
import uuid
from pathlib import Path

from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE

CASES = {
    "op-b17": "warfare_wings:b17",
    "op-escort-left": "warfare_wings:p47n",
    "op-escort-right": "warfare_wings:p47n",
}
SAMPLES = 341
SELECTED_METHOD = "VISIBLE_CPA_TO_PROTECTED_ASSET"
SOURCE_LABEL = "ORIGINAL_FORGE_REAL_FOV_LOS_CONTACT_SELECTION"


def read_reason(reason: str, scenario: str, tick: int) -> dict[str, str]:
    elements = reason.split("|")
    values: dict[str, str] = {}
    for token in elements[1:]:
        if "=" not in token:
            raise ValueError(f"{scenario}:{tick}: malformed measured decision tag")
        key, value = token.split("=", 1)
        if not key or not value or key in values:
            raise ValueError(f"{scenario}:{tick}: missing/duplicate decision tag")
        values[key] = value
    return values


def validate_one(directory: Path, scenario: str, aircraft: str) -> dict:
    path = directory / f"{scenario}-forge-controls.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing original-Forge actor receipt: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{scenario}: forged/unknown real pilot trace schema")
        rows = list(reader)
    if len(rows) != SAMPLES:
        raise ValueError(f"{scenario}: expected 341 actual entity states, got {len(rows)}")
    first, multi, visible, predicted, recordedSelection = -1, 0, 0, 0, 0
    prev_clock = None
    for tick, row in enumerate(rows):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{scenario}:{tick}: malformed real CSV")
        if (row["schema_version"], row["source"], row["scenario_id"], row["aircraft_id"]) != (
                SCHEMA, SOURCE, scenario, aircraft):
            raise ValueError(f"{scenario}:{tick}: not the original visible aircraft receipt")
        if int(row["sim_tick"]) != tick:
            raise ValueError(f"{scenario}:{tick}: omitted original aircraft physics tick")
        clock = int(row["game_time"])
        if prev_clock is not None and clock != prev_clock + 1:
            raise ValueError(f"{scenario}:{tick}: missing real server tick")
        prev_clock = clock
        if tick == 0:
            if row["reason"] != "INITIAL" or row["maneuver"] != "INITIAL":
                raise ValueError(f"{scenario}: no authentic initial flight state")
            continue
        tags = read_reason(row["reason"], scenario, tick)
        if tags.get("live_team") != "convoy" or tags.get("phase") is None:
            raise ValueError(f"{scenario}:{tick}: no observed explicit allied team/phase")
        if tags.get("visible_hostile_count") not in ("0", "1", "2"):
            raise ValueError(f"{scenario}:{tick}: unverified visible-hostile count")
        n = int(tags["visible_hostile_count"])
        sighting = tags.get("sighting", "")
        selection = tags.get("contact_selection")
        if n:
            if selection != SELECTED_METHOD or not sighting.startswith("visible:"):
                raise ValueError(f"{scenario}:{tick}: no safe observed-threat selection")
            # Only IDs from actually acquired sensor contacts qualify. The
            # CSV cannot independently prove LOS; that needs native GameTest.
            try:
                uuid.UUID(sighting.split(":", 1)[1])
            except (IndexError, ValueError) as error:
                raise ValueError(f"{scenario}:{tick}: invalid acquired actor ID") from error
            recordedSelection += 1
            visible += 1
            if n == 2:
                multi += 1
            if first < 0:
                first = tick
        else:
            if selection != "NO_VISIBLE_HOSTILE" or (sighting != "none"
                    and not sighting.startswith("last_seen_prediction:")):
                raise ValueError(f"{scenario}:{tick}: invisible or unsupported opponent state")
            if sighting.startswith("last_seen_prediction:"):
                predicted += 1
    if visible == 0 or multi == 0:
        raise ValueError(f"{scenario}: did not demonstrate actual multi-contact selection")
    return {"scenario": scenario, "aircraft_id": aircraft,
            "synchronized_original_entity_ticks": SAMPLES - 1,
            "first_visible_tick": first, "visible_contact_ticks": visible,
            "two_visible_opponents_ticks": multi,
            "predicted_last_seen_ticks": predicted,
            "verified_selection_ticks": recordedSelection,
            "selector": SELECTED_METHOD}


def verify(directory: Path) -> dict:
    if not directory.is_dir():
        raise FileNotFoundError("Original Forge receipt directory absent")
    cases = [validate_one(directory, scenario, aircraft) for scenario, aircraft in CASES.items()]
    return {"schema_version": "ww.physics.real-observed-asset-threat-selection.v1",
            "evidence": SOURCE_LABEL, "cases": cases,
            "b17_95_block_protection": "NOT_ASSESSED_HERE",
            "autonomous_weapons": "DISABLED_UNPROVEN",
            "conclusion": "ORIGINAL_FORGE_THREE_ACTORS_MULTI_CONTACT_SELECTION_CONFIRMED"}


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("trace_dir", type=Path)
    cli.add_argument("--summary", type=Path)
    args = cli.parse_args()
    try:
        report = verify(args.trace_dir)
    except (OSError, ValueError) as error:
        raise SystemExit("ORIGINAL_FORGE_CONTACT_SELECTION_FAILED: " + str(error)) from None
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

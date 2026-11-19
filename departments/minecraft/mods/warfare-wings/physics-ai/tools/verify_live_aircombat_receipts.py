#!/usr/bin/env python3
"""Independent geometric acceptance of *simultaneous* real Forge flight receipts.

This verifier never replaces a GameTest, claims a kill, or infers unrecorded
weapons. All positions must come from per-vehicle real-Minecraft trace CSVs
with synchronized game ticks. A failing protection gate is a failing result,
even if flight control, sensor or source-only tests otherwise pass.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import sys
from pathlib import Path

from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE

BODY_LIMIT_BLOCKS = 6.0
ESCORT_LIMIT_BLOCKS = 95.0
VALID_KINDS = {"aircombat", "escort"}


class OperationalFailure(ValueError):
    pass


def _finite(value: str, field: str, path: Path, tick: int) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise OperationalFailure(f"{path.name} tick {tick}: nonnumeric {field}") from exc
    if not math.isfinite(number):
        raise OperationalFailure(f"{path.name} tick {tick}: nonfinite {field}")
    return number


def _load_flight(root: Path, flight: dict, expected_ticks: int) -> list[dict]:
    required = {"id", "file", "aircraft_id", "scenario_id", "team"}
    if not isinstance(flight, dict) or not required.issubset(flight):
        raise OperationalFailure(f"Every flight needs {sorted(required)}")
    path = (root / flight["file"]).resolve()
    if not path.is_relative_to(root.resolve()) or path.suffix.lower() != ".csv":
        raise OperationalFailure("Trace must be a .csv beneath the supplied receipt directory")
    if not path.is_file():
        raise OperationalFailure(f"Missing real runtime trace {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise OperationalFailure(f"{path.name}: unexpected Forge trace column schema")
        rows = list(reader)
    if len(rows) != expected_ticks + 1:
        raise OperationalFailure(f"{path.name}: expected {expected_ticks + 1} synchronized samples; got {len(rows)}")
    parsed = []
    unchanged_positions = 0
    for index, row in enumerate(rows):
        if None in row or any(value is None for value in row.values()):
            raise OperationalFailure(f"{path.name}: malformed CSV sample {index}")
        expected = (SCHEMA, SOURCE, flight["scenario_id"], flight["aircraft_id"])
        actual = tuple(row[field] for field in ("schema_version", "source", "scenario_id", "aircraft_id"))
        if actual != expected:
            raise OperationalFailure(f"{path.name} tick {index}: forged/mismatched runtime identity")
        if not row["maneuver"] or not row["reason"] or not row["world_safety_reason"]:
            raise OperationalFailure(f"{path.name} tick {index}: no observed AI decision")
        try:
            tick, game_time = int(row["sim_tick"]), int(row["game_time"])
        except ValueError as exc:
            raise OperationalFailure(f"{path.name} tick {index}: invalid time") from exc
        if tick != index:
            raise OperationalFailure(f"{path.name}: discontinuous simulation tick {index} -> {tick}")
        pos = tuple(_finite(row[f"pos_{axis}"], f"pos_{axis}", path, index) for axis in "xyz")
        velocity = tuple(_finite(row[f"vel_{axis}"], f"vel_{axis}", path, index) for axis in "xyz")
        _finite(row["engine_power"], "engine_power", path, index)
        parsed.append({"tick": tick, "game_time": game_time, "pos": pos, "velocity": velocity})
        if index > 0 and game_time != parsed[index - 1]["game_time"] + 1:
            raise OperationalFailure(f"{path.name}: frozen or skipped game tick {index}")
        # A running fixed-wing engagement must not repeat one physical position
        # while the server clock continues; such tails once corrupted A6M
        # calibration after the aircraft left loaded chunks. Independently
        # reject them even if a faulty producer increments its sample counter.
        if index > 0 and math.dist(pos, parsed[index - 1]["pos"]) <= 1e-9:
            unchanged_positions += 1
            if unchanged_positions >= 3:
                raise OperationalFailure(f"{path.name}: non-moving aircraft physics snapshot at tick {index}")
        else:
            unchanged_positions = 0
    distance = math.dist(parsed[0]["pos"], parsed[-1]["pos"])
    if distance < 8.0:
        raise OperationalFailure(f"{path.name}: aircraft did not demonstrate 8 blocks of real displacement ({distance:.3f})")
    return parsed


def verify(manifest: dict, trace_dir: Path) -> dict:
    if manifest.get("kind") not in VALID_KINDS:
        raise OperationalFailure(f"kind must be one of {sorted(VALID_KINDS)}")
    if manifest.get("source") != SOURCE:
        raise OperationalFailure("Only real Forge next-tick-injection telemetry is accepted")
    ticks = manifest.get("ticks")
    if type(ticks) is not int or not (40 <= ticks <= 10000):
        raise OperationalFailure("Unreasonable/missing measured tick horizon")
    flights = manifest.get("flights")
    if not isinstance(flights, list) or not 2 <= len(flights) <= 64:
        raise OperationalFailure("Expected 2..64 simultaneous aircraft")
    ids = [f.get("id") for f in flights if isinstance(f, dict)]
    files = [f.get("file") for f in flights if isinstance(f, dict)]
    if len(ids) != len(flights) or any(not isinstance(x, str) or not x for x in ids + files):
        raise OperationalFailure("Flight IDs and relative filenames must be nonempty strings")
    if len(set(ids)) != len(ids) or len(set(files)) != len(files):
        raise OperationalFailure("Duplicate flight IDs or receipts")
    for flight in flights:
        for key in ("aircraft_id", "scenario_id", "team"):
            if not isinstance(flight.get(key), str) or not flight[key]:
                raise OperationalFailure(f"Flight {flight['id']}: explicit nonempty {key} required")
    if len({f.get("team") for f in flights}) < 2:
        raise OperationalFailure("No explicitly identified opposing teams")
    data = {f["id"]: _load_flight(trace_dir, f, ticks) for f in flights}
    for tick in range(ticks + 1):
        clocks = {rows[tick]["game_time"] for rows in data.values()}
        if len(clocks) != 1:
            raise OperationalFailure(f"Simultaneous aircraft are not on the same real Minecraft tick: sample {tick}")

    pairs = []
    breaches = []
    for a, b in itertools.combinations(flights, 2):
        d = [math.dist(data[a["id"]][t]["pos"], data[b["id"]][t]["pos"]) for t in range(ticks + 1)]
        minimum = min(d)
        dangerous = sum(value < BODY_LIMIT_BLOCKS for value in d)
        pairs.append({"a": a["id"], "b": b["id"], "closest_blocks": round(minimum, 6),
                      "closest_tick": d.index(minimum), "under_6_blocks_ticks": dangerous})
        if dangerous:
            breaches.append(f"BODY_SEPARATION_LT6:{a['id']}:{b['id']}:ticks={dangerous}")

    assets = []
    if manifest["kind"] == "escort":
        asset_ids = manifest.get("assets")
        assignments = manifest.get("escort_assignments")
        if not isinstance(asset_ids, list) or not asset_ids or len(asset_ids) != len(set(asset_ids)):
            raise OperationalFailure("Escort acceptance requires unique protected asset IDs")
        if not isinstance(assignments, dict) or set(assignments) != set(asset_ids):
            raise OperationalFailure("Escort acceptance requires explicit escort assignment for each asset")
        for asset_id in asset_ids:
            asset = next((f for f in flights if f["id"] == asset_id), None)
            if asset is None:
                raise OperationalFailure(f"Unknown protected asset {asset_id}")
            threats = [f for f in flights if f["team"] != asset["team"]]
            guard_ids = assignments[asset_id]
            if not isinstance(guard_ids, list) or not guard_ids or len(set(guard_ids)) != len(guard_ids):
                raise OperationalFailure(f"{asset_id}: missing or duplicate assigned escort IDs")
            escorts = [f for f in flights if f["id"] in guard_ids and f["team"] == asset["team"] and f["id"] != asset_id]
            if not threats or len(escorts) != len(guard_ids):
                raise OperationalFailure(f"{asset_id}: needs both actual escort and hostile aircraft")
            min_distance = math.inf
            intrusions = 0
            for t in range(ticks + 1):
                nearest = min(math.dist(data[asset_id][t]["pos"], data[threat["id"]][t]["pos"])
                              for threat in threats)
                min_distance = min(min_distance, nearest)
                if nearest < ESCORT_LIMIT_BLOCKS:
                    intrusions += 1
            assets.append({"asset": asset_id, "closest_hostile_blocks": round(min_distance, 6),
                           "hostile_inside_95_blocks_ticks": intrusions})
            if intrusions:
                breaches.append(f"ESCORT_PROTECTION_BREACHED:{asset_id}:ticks={intrusions}")

    return {"schema_version": "ww.physics.forge-multiaircraft-acceptance.v1",
            "evidence": "ACTUAL_SYNCHRONIZED_MINECRAFT_ENTITY_POSITIONS",
            "source": SOURCE, "scenario": manifest.get("scenario"), "kind": manifest["kind"],
            "observed_ticks": ticks, "observed_aircraft": len(flights), "pairs": pairs,
            "protected_assets": assets, "failed_operational_gates": breaches,
            "conclusion": "FAILED" if breaches else "GEOMETRIC_GATES_PASSED_NO_WEAPON_OR_KILL_PROOF"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON describing exact measured real-Forge traces")
    parser.add_argument("trace_dir", type=Path, help="directory containing emitted runtime CSV receipts")
    parser.add_argument("--summary", type=Path, help="write factual operational summary even if safety gates fail")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        result = verify(manifest, args.trace_dir)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ACTUAL_FORGE_RECEIPT_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failed_operational_gates"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

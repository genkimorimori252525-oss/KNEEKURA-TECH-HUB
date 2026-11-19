#!/usr/bin/env python3
"""Independently verify three exact ORIGINAL Forge B-17 attempts, read-only.

Source Twin predictions must never masquerade as a real original GameTest.
Each root is verified using the same strict independent five-actor clock,
geometry and source-provenance gates. It makes no isolated causal claim.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

from forensic_b17_compare import (
    BODY, PROTECTION, REAL_TICK_COUNT, UNITS, ForensicEvidenceError,
    load_verified_real,
)
from forensic_b17_policy_delta import (
    BASE, _real_closest, compare_real_runs,
)

SCHEMA = "ww.physics.real-b17-three-original-runs.v1"
DEFAULT_ROOTS = (
    BASE / "pre-cpa-original-root",
    BASE / "pre-hysteresis-original-root",
    BASE / "ww-physics-traces",
)
LABELS = ("nearest", "protected_asset_cpa", "protected_asset_cpa_retained")


def analyze(roots: tuple[Path, Path, Path], *, quarantine: bool) -> tuple[dict, list[dict]]:
    if len(roots) != 3 or len({r.resolve() for r in roots}) != 3:
        raise ForensicEvidenceError("Three unique owner real GameTest roots required")
    real = [load_verified_real(root, quarantine_stale_sidecar=quarantine) for root in roots]
    # These comparisons validate the same original geometry, source identity,
    # synchronized clock and all five actor receipts, without reimplementing
    # the separate independent operational acceptance logic.
    first_second, _, _ = compare_real_runs(real[0], real[1])
    second_third, _, _ = compare_real_runs(real[1], real[2])
    out = []
    results = []
    for label,record in zip(LABELS,real):
        series = [_real_closest(record,t)[0] for t in range(1,REAL_TICK_COUNT+1)]
        expected = record.sidecar["protected_assets"][0]
        result = {
            "policy_label": label,
            "original_root": record.root.name,
            "real_source": record.sidecar["source"],
            "strict_340_actor_physics_intrusion_ticks": sum(d < PROTECTION for d in series),
            "closest_b17_hostile_in_340_ticks": min(series),
            "native_saved_or_extended_geometry_intrusions": expected["hostile_inside_95_blocks_ticks"],
            "native_operational_verdict": record.sidecar["conclusion"],
            "saved_sidecar_status": record.saved_sidecar_status,
            "original_hashes": dict(sorted(record.sha256.items())),
            "post_control_stale_units_excluded": list(record.excluded_post_control_stale_units),
        }
        if result["strict_340_actor_physics_intrusion_ticks"] < 0:
            raise ForensicEvidenceError("Negative real protection count")
        results.append(result)
    for tick in range(REAL_TICK_COUNT+1):
        row = {"schema": SCHEMA, "tick": tick}
        for label,record in zip(LABELS,real):
            near, closest_actor = _real_closest(record,tick)
            row[f"{label}_closest_b17_raider_blocks"] = round(near,9)
            row[f"{label}_closest_actor"] = closest_actor
            row[f"{label}_strict_inside95"] = tick > 0 and near < PROTECTION
            for unit in UNITS:
                actor=record.traces[unit][tick]
                row[f"{label}_{unit}_raw_x"] = actor["command_x"]
                row[f"{label}_{unit}_raw_z"] = actor["command_z"]
        out.append(row)
    summary = {
        "schema": SCHEMA,
        "evidence": "THREE_INDEPENDENT_ORIGINAL_REAL_MINECRAFT_ENTITY_RECORDINGS_NO_SOURCE_SUBSTITUTES",
        "actor_count_per_original_game_test": len(UNITS),
        "synchronized_actor_physics_ticks": REAL_TICK_COUNT,
        "min_pair_separation_gate_blocks": BODY,
        "b17_zero_intrusion_gate_blocks": PROTECTION,
        "runs": results,
        "nearest_to_cpa_first_changed_control_by_actor": {
            r["unit_id"]: r["first_real_controller_input_difference_tick"]
            for r in first_second["per_unit"]
        },
        "cpa_to_retained_first_changed_control_by_actor": {
            r["unit_id"]: r["first_real_controller_input_difference_tick"]
            for r in second_third["per_unit"]
        },
        "warnings": [
            "Archive native extended geometry may include a 341st post-controller sample; compare actor physics ticks 1..340 only",
            "Each source/provenance/clock and starting geometry independently verified; stale sidecars quarantined",
            "This observational comparison does NOT isolate the causes of policy changes, nor prove tactical victory",
            "No original game JAR or measured CSV body is included in this output",
        ],
    }
    return summary,out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nearest-real",type=Path,default=DEFAULT_ROOTS[0])
    parser.add_argument("--cpa-real",type=Path,default=DEFAULT_ROOTS[1])
    parser.add_argument("--retained-real",type=Path,default=DEFAULT_ROOTS[2])
    parser.add_argument("--quarantine-stale-sidecars",action="store_true")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    roots=(args.nearest_real,args.cpa_real,args.retained_real)
    output=args.output.resolve()
    try:
        for root in roots:
            resolved=root.resolve()
            if output==resolved or resolved in output.parents:
                raise ForensicEvidenceError("Cannot overwrite or write inside owner REAL receipt folder")
        summary,frames=analyze(roots,quarantine=args.quarantine_stale_sidecars)
        output.mkdir(parents=True,exist_ok=True)
        (output/"three-real-b17-policies.json").write_text(
            json.dumps(summary,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+"\n",
            encoding="utf-8",newline="\n")
        with (output/"three-real-b17-policies-ticks.csv").open(
                "w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(frames[0]))
            writer.writeheader()
            writer.writerows(frames)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("THREE_REAL_FORGE_POLICY_FAILED: "+str(exc),file=sys.stderr)
        raise SystemExit(2) from None
    print("THREE_ORIGINAL_FORGE_B17_POLICY_ATTEMPTS_VERIFIED "
          + " ".join(f'{s["policy_label"]}='
                     f'{s["strict_340_actor_physics_intrusion_ticks"]}/340'
                     for s in summary["runs"]) + " NO_B17_VICTORY_NOT_CAUSAL_PROOF")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare two complete ORIGINAL REAL Forge B17 operational GameTest runs.

Independent per-run provenance/time/geometry checks are identical to the
real-vs-SOURCE tool. This is a REAL-vs-REAL descriptive policy investigation:
no generated SOURCE positions count as REAL, no historical sidecar that
disagrees with the real pilot CSV is silently accepted.

For current owner-local receipt folders that retained an OLD sidecar JSON,
an explicit --quarantine-stale-sidecars flag recomputes real acceptance
from original 5*341 Forge CSV rows while retaining the stale file's SHA-256
in the rejected/quarantined sidecar audit namespace.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from forensic_b17_compare import (
    BODY, PROTECTION, REAL_TICK_COUNT, REAL_SCENE, UNITS,
    ForensicEvidenceError, RealReceipts, _dist, _real_reason,
    _vec, _write_csv, load_verified_real,
)
from flight_lab_run import MODULE

SCHEMA="ww.flight-twin.real-b17-policy-delta.v1"
BASE=MODULE/"runtime-probe"/"run-gametest"
DEFAULT_BEFORE=BASE/"pre-cpa-original-root"
DEFAULT_AFTER=BASE/"ww-physics-traces"


def _real_closest(data: RealReceipts, tick: int) -> tuple[float,str]:
    b17=data.traces["b17"][tick]["position"]
    threats=[(_dist(b17,data.traces[u][tick]["position"]),u)
             for u in ("raider-1","raider-2")]
    return min(threats)


def _minimum_pair(data: RealReceipts,tick: int) -> tuple[float,str]:
    pairs=[]
    for i,u in enumerate(UNITS):
        for v in UNITS[i+1:]:
            distance=_dist(data.traces[u][tick]["position"],
                           data.traces[v][tick]["position"])
            pairs.append((distance,u+"|"+v))
    return min(pairs)


def _position_error(before: RealReceipts,after: RealReceipts,
                    unit: str,tick: int) -> float:
    b=_vec(before.traces[unit][tick],True,before.coordinate_anchor)
    a=_vec(after.traces[unit][tick],True,after.coordinate_anchor)
    return math.dist(b,a)


def compare_real_runs(before: RealReceipts,after: RealReceipts) -> tuple[dict,list[dict],list[dict]]:
    """Never infer policy causation from correlated trajectory differences."""
    if before.manifest!=after.manifest:
        raise ForensicEvidenceError("Before/after Forge manifests differ")
    for unit in UNITS:
        b,a=before.traces[unit][0],after.traces[unit][0]
        for axis in ("yaw_deg","pitch_deg","vel_x","vel_y","vel_z"):
            if abs(float(b[axis])-float(a[axis]))>1e-7:
                raise ForensicEvidenceError(
                    f"Cannot compare different real initial controls ({unit}:{axis})")
        if _position_error(before,after,unit,0)>1e-6:
            raise ForensicEvidenceError(
                "Before/after REAL scenario does not preserve the original same start geometry")
    ticks:list[dict]=[]
    per_unit:list[dict]=[]
    prev={}
    for tick in range(REAL_TICK_COUNT+1):
        bmin,bthreat=_real_closest(before,tick)
        amin,athreat=_real_closest(after,tick)
        bpair,bpairid=_minimum_pair(before,tick)
        apair,apairid=_minimum_pair(after,tick)
        ticks.append({
            "schema":SCHEMA,"tick":tick,"seconds":round(tick/20,5),
            "before_real_game_time":before.game_time_zero+tick,
            "after_real_game_time":after.game_time_zero+tick,
            "before_min_hostile_to_b17_blocks":round(bmin,9),
            "after_min_hostile_to_b17_blocks":round(amin,9),
            "after_minus_before_threat_distance_blocks":round(amin-bmin,9),
            "before_nearest_raider":bthreat,"after_nearest_raider":athreat,
            "before_inside95_strict":bmin<PROTECTION,
            "after_inside95_strict":amin<PROTECTION,
            "before_global_min_pair_blocks":round(bpair,9),
            "after_global_min_pair_blocks":round(apair,9),
            "before_closest_pair":bpairid,"after_closest_pair":apairid,
            "before_under6":bpair<BODY,"after_under6":apair<BODY,
            "real_tick_explanation":(
                f"At REAL common tick {tick}, independently measured BEFORE "
                f"B17 nearest {bthreat}={bmin:.3f} blocks "
                f"({'INSIDE' if bmin<PROTECTION else 'OUTSIDE'} strict 95b); "
                f"AFTER nearest {athreat}={amin:.3f} blocks "
                f"({'INSIDE' if amin<PROTECTION else 'OUTSIDE'} strict 95b). "
                f"Nearest-threat difference AFTER-BEFORE {amin-bmin:+.3f} blocks. "
                f"Both are original synchronized Forge GameTest entities; "
                f"this association cannot isolate the causal effect of a code change.")
        })
        for unit in UNITS:
            b,a=before.traces[unit][tick],after.traces[unit][tick]
            br,ar=_real_reason(b),_real_reason(a)
            before_control=tuple(float(b[f]) for f in (
                "command_x","command_z","command_throttle"))
            after_control=tuple(float(a[f]) for f in (
                "command_x","command_z","command_throttle"))
            differences=tuple(after_control[i]-before_control[i] for i in range(3))
            distance=_position_error(before,after,unit,tick)
            unit_row={
                "schema":SCHEMA,"tick":tick,"seconds":round(tick/20,5),
                "unit_id":unit,"aircraft_id":b["aircraft_id"],
                "before_x_relative":round(_vec(b,True,before.coordinate_anchor)[0],9),
                "before_y":round(b["position"][1],9),
                "before_z_relative":round(_vec(b,True,before.coordinate_anchor)[2],9),
                "after_x_relative":round(_vec(a,True,after.coordinate_anchor)[0],9),
                "after_y":round(a["position"][1],9),
                "after_z_relative":round(_vec(a,True,after.coordinate_anchor)[2],9),
                "position_divergence_blocks":round(distance,9),
                "before_speed_bps":round(math.dist((0,0,0),b["velocity"])*20,9),
                "after_speed_bps":round(math.dist((0,0,0),a["velocity"])*20,9),
                "before_maneuver":b["maneuver"],
                "after_maneuver":a["maneuver"],
                "before_sighting":br["sighting"],
                "after_sighting":ar["sighting"],
                "before_phase":br["phase"],
                "after_phase":ar["phase"],
                "before_reason_code":br["reason_code"],
                "after_reason_code":ar["reason_code"],
                "before_safety_reason":b["world_safety_reason"],
                "after_safety_reason":a["world_safety_reason"],
                "before_control_x":before_control[0],
                "before_control_z":before_control[1],
                "before_control_throttle":before_control[2],
                "after_control_x":after_control[0],
                "after_control_z":after_control[1],
                "after_control_throttle":after_control[2],
                "delta_control_x":round(differences[0],9),
                "delta_control_z":round(differences[1],9),
                "delta_control_throttle":round(differences[2],9),
                "maneuver_changed":b["maneuver"]!=a["maneuver"],
                "sighting_changed":br["sighting"]!=ar["sighting"],
                "phase_changed":br["phase"]!=ar["phase"],
                "changed_policy_input":any(abs(v)>1e-5 for v in differences),
                "unit_tick_explanation":(
                    f"At REAL tick {tick}, {unit} BEFORE saw {br['sighting']} "
                    f"with phase={br['phase']}, maneuver={b['maneuver']}, "
                    f"raw x/z/throttle={before_control[0]:+.3f}/"
                    f"{before_control[1]:+.3f}/{before_control[2]:.3f}; "
                    f"AFTER saw {ar['sighting']}, phase={ar['phase']}, "
                    f"maneuver={a['maneuver']}, control="
                    f"{after_control[0]:+.3f}/{after_control[1]:+.3f}/"
                    f"{after_control[2]:.3f}. Relative position differs "
                    f"{distance:.3f} blocks. Differences may result from"
                    " changed contacts, policy and earlier physical trajectories,"
                    " not a single isolated new manoeuvre.")
            }
            per_unit.append(unit_row)

    before_saved=before.saved_sidecar_status
    after_saved=after.saved_sidecar_status
    first_before=next((r["tick"] for r in ticks if r["before_inside95_strict"]),None)
    first_after=next((r["tick"] for r in ticks if r["after_inside95_strict"]),None)
    unit_summary=[]
    for unit in UNITS:
        subset=[r for r in per_unit if r["unit_id"]==unit]
        changed=[r for r in subset[1:] if r["changed_policy_input"]]
        phase=[r for r in subset[1:] if r["phase_changed"]]
        sight=[r for r in subset[1:] if r["sighting_changed"]]
        distance=[r["position_divergence_blocks"] for r in subset]
        unit_summary.append({
            "unit_id":unit,"aircraft_id":subset[0]["aircraft_id"],
            "first_real_controller_input_difference_tick":
                changed[0]["tick"] if changed else None,
            "ticks_with_distinct_raw_input":len(changed),
            "first_phase_difference_tick":phase[0]["tick"] if phase else None,
            "first_sighting_class_difference_tick":sight[0]["tick"] if sight else None,
            "before_visible_ticks":sum(r["before_sighting"]=="VISIBLE_UUID" for r in subset[1:]),
            "after_visible_ticks":sum(r["after_sighting"]=="VISIBLE_UUID" for r in subset[1:]),
            "final_real_position_difference_blocks":round(distance[-1],9),
            "max_real_position_difference_blocks":round(max(distance),9),
        })

    before_asset=before.sidecar["protected_assets"][0]
    after_asset=after.sidecar["protected_assets"][0]
    summary={
        "schema":SCHEMA,"comparison":"BEFORE_AND_AFTER_TWO_INDEPENDENT_REAL_FORGE_GAME_TESTS",
        "evidence":"TWO_SEPARATELY_VERIFIED_ACTUAL_MINECRAFT_ENTITY_POSITION_STREAMS",
        "ticks":REAL_TICK_COUNT,"unit_count":5,"tick_hz":20,
        "physical_distance_limit_blocks":BODY,"b17_protection_limit_blocks":PROTECTION,
        "before":{
            "root_label":before.root.name,
            "original_saved_sidecar_status":before_saved,
            "real_acceptance_recomputed":before.sidecar["conclusion"],
            "source":"minecraft_runtime_ia_next_tick_injection",
            "real_game_time_zero":before.game_time_zero,
            "sha256_by_original_real_filename":dict(sorted(before.sha256.items())),
            "min_b17_raider_distance_blocks":before_asset["closest_hostile_blocks"],
            "strict_inside95_ticks":before_asset["hostile_inside_95_blocks_ticks"],
            "first_inside95_tick":first_before,
            "body_lt6_pair_ticks":sum(p["under_6_blocks_ticks"] for p in before.sidecar["pairs"]),
            "excluded_extra_post_control_stale_units":
                list(before.excluded_post_control_stale_units),
        },
        "after":{
            "root_label":after.root.name,
            "original_saved_sidecar_status":after_saved,
            "real_acceptance_recomputed":after.sidecar["conclusion"],
            "source":"minecraft_runtime_ia_next_tick_injection",
            "real_game_time_zero":after.game_time_zero,
            "sha256_by_original_real_filename":dict(sorted(after.sha256.items())),
            "min_b17_raider_distance_blocks":after_asset["closest_hostile_blocks"],
            "strict_inside95_ticks":after_asset["hostile_inside_95_blocks_ticks"],
            "first_inside95_tick":first_after,
            "body_lt6_pair_ticks":sum(p["under_6_blocks_ticks"] for p in after.sidecar["pairs"]),
            "excluded_extra_post_control_stale_units":
                list(after.excluded_post_control_stale_units),
        },
        "change":{
            "after_minus_before_inside95_ticks":
                after_asset["hostile_inside_95_blocks_ticks"]
                -before_asset["hostile_inside_95_blocks_ticks"],
            "after_minus_before_min_raider_distance_blocks":round(
                after_asset["closest_hostile_blocks"]-
                before_asset["closest_hostile_blocks"],9),
            "after_minus_before_first_intrusion_tick":
                first_after-first_before
                if first_after is not None and first_before is not None else None,
        },
        "per_unit":unit_summary,
        "interpretation_limits":[
            "Sidecars that disagree with REAL CSV are quarantined, NEVER trusted.",
            "This is REAL BEFORE vs REAL AFTER, not SOURCE simulation evidence.",
            "Changed controls and divergence are observationally associated; they do not isolate one code change.",
            "REAL aircraft chunk liveness, weapon effects and GameTest objective acceptance retain separate gates.",
        ],
    }
    return summary,ticks,per_unit


def save_policy_delta(output: Path,summary: dict,
                      frames: list[dict],units: list[dict]) -> None:
    output.mkdir(parents=True,exist_ok=True)
    (output/"forensic_b17_real_policy_delta.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False,
                   allow_nan=False,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    _write_csv(output/"forensic_b17_real_policy_ticks.csv",frames)
    _write_csv(output/"forensic_b17_real_policy_units.csv",units)
    before=summary["before"]
    after=summary["after"]
    change=summary["change"]
    lines=[
        "# Two REAL Forge B-17 GameTests: before and after policy forensics",
        "",
        "These are **two independently verified REAL Minecraft/Forge entity "
        "streams**, not synthetic aircraft data. Existing stale saved acceptance "
        "JSON files were explicitly quarantined and their SHA-256 retained.",
        "",
        "| Measurement | Before REAL | After REAL |",
        "|---|---:|---:|",
        f"| Protection <95 blocks duration | {before['strict_inside95_ticks']} ticks | "
        f"{after['strict_inside95_ticks']} ticks |",
        f"| First intrusion tick | {before['first_inside95_tick']} | "
        f"{after['first_inside95_tick']} |",
        f"| Minimum B17-to-raider distance | "
        f"{before['min_b17_raider_distance_blocks']:.3f} b | "
        f"{after['min_b17_raider_distance_blocks']:.3f} b |",
        f"| Body proximity <6-block pair ticks | {before['body_lt6_pair_ticks']} | "
        f"{after['body_lt6_pair_ticks']} |",
        f"| Independently recomputed acceptance | {before['real_acceptance_recomputed']} | "
        f"{after['real_acceptance_recomputed']} |",
        "",
        f"Change: **{change['after_minus_before_inside95_ticks']:+d} ticks** inside "
        f"95b, **{change['after_minus_before_min_raider_distance_blocks']:+.3f} "
        "blocks** of minimum hostile-to-B17 separation.",
        "",
        "| Airframe | First divergent raw control tick | Distinct-control ticks "
        "| First phase difference | First sighting difference | Final position separation |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary["per_unit"]:
        lines.append(f"| {row['unit_id']} | {row['first_real_controller_input_difference_tick']} "
            f"| {row['ticks_with_distinct_raw_input']} | "
            f"{row['first_phase_difference_tick']} | "
            f"{row['first_sighting_class_difference_tick']} | "
            f"{row['final_real_position_difference_blocks']:.3f} b |")
    lines.extend([
        "",
        "## Chronology and causal limits",
        "",
        "The next CSV has 341 dual-REAL nearest-threat measurements and the unit CSV "
        "has all 1,705 paired controller states with human-readable explanations.",
        "The old saved JSON in the before/after directories did NOT match the "
        "corresponding 340-tick CSV. The comparator never used those stale numbers "
        "as the acceptance result; each GameTest is verified again from REAL "
        "simulated tick, game clock, velocity and position observations.",
        "A change in observed sighting can change a command, which changes future "
        "position, which changes subsequent observations. The recorded differences "
        "therefore show association over two real deployments but cannot "
        "scientifically attribute deterioration to one isolated code branch "
        "without a controlled ablation experiment.",
    ])
    (output/"forensic_b17_real_policy_findings.md").write_text(
        "\n".join(lines)+"\n",encoding="utf-8",newline="\n")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-real-dir",type=Path,default=DEFAULT_BEFORE)
    parser.add_argument("--after-real-dir",type=Path,default=DEFAULT_AFTER)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--quarantine-stale-sidecars",action="store_true",
                        help="Explicitly discard unmatching saved sidecar totals; "
                             "accept only independently recomputed genuine REAL CSV metrics")
    args=parser.parse_args()
    try:
        before=load_verified_real(args.before_real_dir,
                                  quarantine_stale_sidecar=args.quarantine_stale_sidecars)
        after=load_verified_real(args.after_real_dir,
                                 quarantine_stale_sidecar=args.quarantine_stale_sidecars)
        output=args.output.resolve()
        for root in (before.root,after.root):
            if root==output or root in output.parents:
                raise ForensicEvidenceError("Cannot write analysis over original REAL receipt folder")
        summary,frames,units=compare_real_runs(before,after)
        save_policy_delta(output,summary,frames,units)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("REAL_FORGE_BEFORE_AFTER_REJECTED: "+str(exc),file=sys.stderr)
        raise SystemExit(2) from None
    change=summary["change"]
    print("REAL_FORGE_BEFORE_AFTER_VALIDATED real_scenarios=2 units=5 ticks=340")
    print(f"BEFORE_REAL <95={summary['before']['strict_inside95_ticks']} "
          f"min={summary['before']['min_b17_raider_distance_blocks']:.6f}b "
          f"quarantine={summary['before']['original_saved_sidecar_status']}")
    print(f"AFTER_REAL <95={summary['after']['strict_inside95_ticks']} "
          f"min={summary['after']['min_b17_raider_distance_blocks']:.6f}b "
          f"quarantine={summary['after']['original_saved_sidecar_status']}")
    print(f"CHANGE <95={change['after_minus_before_inside95_ticks']:+d} ticks "
          f"min_hostile_distance={change['after_minus_before_min_raider_distance_blocks']:+.6f}b "
          "attribution=OBSERVATIONAL_ONLY")


if __name__=="__main__":
    main()

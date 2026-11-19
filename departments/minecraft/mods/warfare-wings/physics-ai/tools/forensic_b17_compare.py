#!/usr/bin/env python3
"""Reconcile the ORIGINAL 340-tick real Forge B-17 receipt and 20Hz closed-loop SOURCE twin.

Read-only original ignored game receipts; no generated file is called REAL.
The independent existing Forge verifier is re-run before comparison, and the
original acceptance sidecar and geometry trace must agree with actual per-airframe
CSV columns, identity, clocks and positions. Missing/fabricated SOURCE markers
or frozen/short REAL files fail closed.

This compares an AUTONOMOUS closed-loop source run, not a teacher-forced replay:
sensor, tactical policy, world terrain, input timing and physical movement may
all differ. Absolute position errors are therefore COMBINED divergences and do
NOT isolate a physics defect or promote SOURCE results into REAL evidence.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from hashlib import sha256
from html import escape as html_escape
import json
import math
from pathlib import Path
import re
import statistics
import sys
import tempfile

from verify_live_aircombat_receipts import verify as verify_actual_forge
from verify_live_aircombat_receipts import OperationalFailure
from verify_tactical_runtime_receipts import COLUMNS as FORGE_COLUMNS
from verify_tactical_runtime_receipts import SCHEMA as FORGE_SCHEMA
from verify_tactical_runtime_receipts import SOURCE as FORGE_SOURCE
from flight_lab_report import load_twin_experiment
from flight_lab_run import MODULE, compile_lab, get_java17, run_twin

SCENE = "forge_original_b17_340"
REAL_SCENE = "operational-b17-escort"
RECONCILIATION_SCHEMA = "ww.flight-twin.forge-b17-forensic.v1"
FORGE_EVIDENCE = "ACTUAL_SYNCHRONIZED_MINECRAFT_ENTITY_POSITIONS"
TWIN_EVIDENCE = "SOURCE_TICK_WITH_REACTION_PINNED_IA133_WIND_SYNTHETIC_SENSORS_NO_FORGE_PARITY"
REAL_SIDECAR_SCHEMA = "ww.physics.forge-multiaircraft-acceptance.v1"
GEOMETRY_SCHEMA = "ww.physics.operational.geometry.v1"
EXACT_NUMERIC_FIELDS = ("pos_x","pos_y","pos_z","vel_x","vel_y","vel_z",
                        "yaw_deg","pitch_deg","engine_power","engine_target",
                        "command_x","command_z","command_throttle")
UNITS = ("b17","escort-left","escort-right","raider-1","raider-2")
REAL_TICK_COUNT = 340
BODY = 6.0
PROTECTION = 95.0
DEFAULT_REAL = (MODULE / "runtime-probe" / "run-gametest"
                / "original-root-receipts-20261011-preserved")
DEFAULT_MANIFEST = MODULE / "scenarios" / "forge-operational-b17-escort.json"


class ForensicEvidenceError(ValueError):
    """A required original-real receipt is missing, inconsistent or untrusted."""


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _finite(value: str | float, context: str) -> float:
    try:
        n = float(value)
    except (ValueError, TypeError) as exc:
        raise ForensicEvidenceError(f"{context}: invalid numeric value") from exc
    if not math.isfinite(n):
        raise ForensicEvidenceError(f"{context}: nonfinite value")
    return n


def _strict_int(value: str, context: str) -> int:
    try:
        n = int(value)
    except (ValueError, TypeError) as exc:
        raise ForensicEvidenceError(f"{context}: invalid integer") from exc
    if str(n) != value:
        raise ForensicEvidenceError(f"{context}: noncanonical integer")
    return n


def _read_csv(path: Path, expected_header: list[str] | None = None) -> list[dict[str,str]]:
    if not path.is_file():
        raise ForensicEvidenceError(f"Missing original REAL file {path}")
    with path.open(encoding="utf-8-sig",newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or (expected_header is not None
                and reader.fieldnames != expected_header):
            raise ForensicEvidenceError(f"{path.name}: exact CSV header does not match")
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ForensicEvidenceError(f"{path.name}: malformed CSV row")
        return rows


@dataclass
class RealReceipts:
    manifest: dict
    sidecar: dict
    traces: dict[str,list[dict]]
    geometry: dict[int,dict[str,dict]]
    root: Path
    sha256: dict[str,str]
    coordinate_anchor: tuple[float,float,float]
    game_time_zero: int
    geometry_extra_sample: int
    saved_sidecar_status: str
    excluded_post_control_stale_units: tuple[str,...]


def load_verified_real(root: Path, manifest_path: Path = DEFAULT_MANIFEST,
                       *, quarantine_stale_sidecar: bool = False) -> RealReceipts:
    """Uses existing independent real-Forge verifier as an authoritative gate."""
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not root.is_dir() or not manifest_path.is_file():
        raise ForensicEvidenceError("Original real receipt folder and manifest must exist")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ForensicEvidenceError("Malformed real Forge manifest") from exc
    if manifest.get("source") != FORGE_SOURCE or manifest.get("scenario") != REAL_SCENE \
            or manifest.get("kind") != "escort" or manifest.get("ticks") != REAL_TICK_COUNT \
            or manifest.get("assets") != ["b17"] \
            or manifest.get("escort_assignments") != {
                "b17": ["escort-left","escort-right"]
            }:
        raise ForensicEvidenceError("Wrong real Forge B-17 340tick manifest identity")
    declared = {f["id"]:f for f in manifest.get("flights",[])
                if isinstance(f,dict) and "id" in f}
    if set(declared) != set(UNITS) or len(manifest["flights"]) != len(UNITS):
        raise ForensicEvidenceError("Expected exactly the five ORIGINAL real B17 aircraft")
    original_types = {
        "b17":"warfare_wings:b17",
        "escort-left":"warfare_wings:p47n",
        "escort-right":"warfare_wings:p47n",
        "raider-1":"warfare_wings:a6m",
        "raider-2":"warfare_wings:a6m",
    }
    teams = {"b17":"convoy","escort-left":"convoy","escort-right":"convoy",
             "raider-1":"raiders","raider-2":"raiders"}
    for unit in UNITS:
        spec = declared[unit]
        if (spec.get("aircraft_id") != original_types[unit]
                or spec.get("team") != teams[unit]
                or spec.get("scenario_id") != "op-"+unit
                or spec.get("file") != f"op-{unit}-forge-controls.csv"):
            raise ForensicEvidenceError(f"Original real B17 manifest airframe identity mismatch: {unit}")

    try:
        independently_verified = verify_actual_forge(manifest,root)
    except (OperationalFailure, OSError, KeyError, TypeError) as exc:
        raise ForensicEvidenceError(f"Independent REAL Forge receipt validation FAILED: {exc}") from exc
    sidecar_file = root/"operational-b17-final.json"
    if not sidecar_file.is_file():
        raise ForensicEvidenceError("Missing ORIGINAL real Forge acceptance sidecar")
    try:
        sidecar = json.loads(sidecar_file.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ForensicEvidenceError("Malformed REAL B17 acceptance sidecar") from exc
    if (sidecar.get("schema_version") != REAL_SIDECAR_SCHEMA
            or sidecar.get("source") != FORGE_SOURCE
            or sidecar.get("evidence") != FORGE_EVIDENCE):
        raise ForensicEvidenceError("REAL saved sidecar has invalid source identity")
    saved_sidecar_status = ("MATCHES_VERIFIED_REAL_CSV"
                            if sidecar == independently_verified
                            else "STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED")
    if sidecar != independently_verified and not quarantine_stale_sidecar:
        raise ForensicEvidenceError(
            "REAL receipt sidecar disagrees with independently recomputed 340tick acceptance")
    # Even when an explicit forensic audit opt-in accepts an internally stale
    # summary file, its OLD result is quarantined and NEVER used as truth.
    # All REAL metrics below come from the original CSV-independent verifier.
    sidecar = independently_verified
    sha = {manifest_path.name:_sha(manifest_path),sidecar_file.name:_sha(sidecar_file)}
    data = {}
    for unit in UNITS:
        spec = declared[unit]
        path = (root/spec["file"]).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() != ".csv":
            raise ForensicEvidenceError("REAL receipt escaped selected input directory")
        rows = _read_csv(path,FORGE_COLUMNS)
        if len(rows) != REAL_TICK_COUNT+1:
            raise ForensicEvidenceError(f"REAL flight {unit} has incomplete 340tick traces")
        parsed = []
        for tick,row in enumerate(rows):
            if (row["schema_version"],row["source"],row["scenario_id"],row["aircraft_id"]) != (
                    FORGE_SCHEMA,FORGE_SOURCE,spec["scenario_id"],spec["aircraft_id"]):
                raise ForensicEvidenceError(f"REAL flight provenance mismatch {unit}@{tick}")
            if _strict_int(row["sim_tick"],f"{unit} sim_tick") != tick:
                raise ForensicEvidenceError(f"REAL flight clock gap {unit}@{tick}")
            position = tuple(_finite(row["pos_"+axis],f"{unit}@{tick}") for axis in "xyz")
            velocity = tuple(_finite(row["vel_"+axis],f"{unit}@{tick}") for axis in "xyz")
            for key in EXACT_NUMERIC_FIELDS:
                _finite(row[key],f"{unit}@{tick}/{key}")
            if not row["maneuver"] or not row["reason"] or not row["world_safety_reason"]:
                raise ForensicEvidenceError(f"Missing REAL decision evidence {unit}@{tick}")
            parsed.append({**row,"tick":tick,"game_time":_strict_int(
                row["game_time"],f"{unit}@{tick}/game_time"),
                "position":position,"velocity":velocity})
        data[unit] = parsed
        sha[path.name] = _sha(path)
    clock_zero = data["b17"][0]["game_time"]
    for tick in range(REAL_TICK_COUNT+1):
        actual = {data[unit][tick]["game_time"] for unit in UNITS}
        if actual != {clock_zero+tick}:
            raise ForensicEvidenceError(f"Mixed or interrupted REAL game tick t={tick}: {actual}")

    geometry_path = root/"operational-b17-escort-geometry.csv"
    geometries = _read_csv(geometry_path,[
        "schema","scenario_id","game_time","sample","aircraft_id","team",
        "entity_tick","pos_x","pos_y","pos_z","closest_enemy",
        "dist_to_b17","observed_ticks","escort_ticks","phase"])
    if len(geometries) not in (REAL_TICK_COUNT*5,(REAL_TICK_COUNT+1)*5):
        raise ForensicEvidenceError("Original independent Forge geometry lacks continuous 340ticks")
    geometry: dict[int,dict[str,dict]] = {}
    excluded_post_control_stale_units: list[str] = []
    for row in geometries:
        if row["schema"] != GEOMETRY_SCHEMA or row["scenario_id"] != REAL_SCENE:
            raise ForensicEvidenceError("Independent geometry is not original REAL Forge")
        sample = _strict_int(row["sample"],"geometry sample")
        game_time = _strict_int(row["game_time"],"geometry game_time")
        entity_tick = _strict_int(row["entity_tick"],"geometry entity_tick")
        if sample < 1 or sample > REAL_TICK_COUNT+1:
            raise ForensicEvidenceError("Geometry sample outside original 340tick replay range")
        if game_time != clock_zero+sample:
            raise ForensicEvidenceError(f"Geometry clock not synchronized with REAL pilots sample={sample}")
        if entity_tick != sample:
            if sample == REAL_TICK_COUNT+1 and entity_tick == REAL_TICK_COUNT:
                # The geometry producer sampled one extra server tick after
                # all five control receipts ended. A late/chunk-stalled unit
                # may still have entityTick=340, which MUST NOT be treated
                # as a verified complete 341st synchronized flight step.
                excluded_post_control_stale_units.append(row["aircraft_id"])
            else:
                raise ForensicEvidenceError(
                    f"Geometry actor tick not synchronized inside REAL control horizon: {sample}")
        unit = row["aircraft_id"]
        if unit not in UNITS or row["team"] != declared[unit]["team"]:
            raise ForensicEvidenceError(f"Geometry contains unknown/nonteam REAL unit {unit}")
        positions = tuple(_finite(row["pos_"+a],f"geometry@{sample}") for a in "xyz")
        for key in ("closest_enemy","dist_to_b17"):
            _finite(row[key],f"geometry@{sample}/{key}")
        record = {**row,"position":positions}
        if unit in geometry.setdefault(sample,{}):
            raise ForensicEvidenceError(f"Repeated geometry unit sample={sample}/{unit}")
        geometry[sample][unit] = record
    if set(geometry) != set(range(1,len(geometries)//5+1)):
        raise ForensicEvidenceError("Independent geometry sample ticks are incomplete")
    for sample, members in geometry.items():
        if set(members) != set(UNITS):
            raise ForensicEvidenceError(f"Independent geometry snapshot not 5 simultaneous entities at {sample}")
        if sample <= REAL_TICK_COUNT:
            for unit in UNITS:
                if math.dist(members[unit]["position"],data[unit][sample]["position"]) > 2e-6:
                    raise ForensicEvidenceError(
                        f"Independent REAL geometry mismatches physical pilot position t={sample} {unit}")
    sha[geometry_path.name] = _sha(geometry_path)
    # Source receipts can be regenerated while this audit is running.
    # Detect modifications between independent verification, inspection
    # and hashing; require an actual frozen, self-consistent REAL snapshot.
    for filename,expected_hash in sha.items():
        actual_path = (manifest_path if filename==manifest_path.name else root/filename)
        if _sha(actual_path)!=expected_hash:
            raise ForensicEvidenceError(
                f"Original REAL receipt changed during forensic verification: {filename}")
    return RealReceipts(manifest,sidecar,data,geometry,root,sha,
                        data["b17"][0]["position"],clock_zero,
                        len(geometries)//5-REAL_TICK_COUNT,
                        saved_sidecar_status,
                        tuple(sorted(excluded_post_control_stale_units)))


def _vec(record: dict, is_real: bool, origin: tuple[float,float,float]) -> tuple[float,float,float]:
    if is_real:
        return (record["position"][0]-origin[0],
                record["position"][1],record["position"][2]-origin[2])
    return record["x"],record["y"],record["z"]


def _dist(a: tuple[float,float,float],b: tuple[float,float,float]) -> float:
    return math.dist(a,b)


def _angle_diff(a: float,b: float) -> float:
    return ((a-b+180)%360)-180


def _real_reason(row: dict) -> dict:
    full=row["reason"]
    pieces=full.split("|")
    params=dict(segment.split("=",1) for segment in pieces[1:] if "=" in segment)
    raw_sighting=params.get("sighting","UNRECORDED")
    if raw_sighting.startswith("visible:"):
        sight="VISIBLE_UUID"
    elif raw_sighting.startswith("track:") or raw_sighting.startswith("memory:"):
        sight="MEMORY"
    elif raw_sighting == "none":
        sight="NONE"
    else:
        sight=raw_sighting.split(":",1)[0].upper()
    return {"reason_code":pieces[0],"sighting":sight,
            "sighting_raw":raw_sighting,"phase":params.get("phase","UNKNOWN"),
            "phase_reason":params.get("phase_reason","UNKNOWN")}


def _source_phase_estimate(row: dict) -> str:
    maneuver=row["maneuver"]
    if maneuver.startswith("TERRAIN") or maneuver=="COLLISION_AVOID":
        return "SOURCE_SAFETY_MANEUVER"
    if maneuver in {"ESCORT_SCREEN","FORMATION_HOLD","COMBAT_BOX_HOLD","FINGER_FOUR_HOLD"}:
        return "SOURCE_ESCORT_OR_FORMATION"
    if maneuver in {"INTERCEPT","TURN_PURSUIT","HIGH_SIDE_PASS","EXTEND_AND_REENTER",
                    "DEFENSIVE_BREAK"}:
        return "SOURCE_COMBAT_MANEUVER"
    return "SOURCE_PATROL_OR_MISSION"


def load_source_twin(output: Path) -> tuple[dict,dict[str,list[dict]],dict]:
    try:
        payload=load_twin_experiment(output)
    except (ValueError,KeyError) as exc:
        raise ForensicEvidenceError(
            f"SOURCE Twin cannot become REAL evidence; NO_FORGE_PARITY/schema verification failed: {exc}") from exc
    summary=payload["summary"]
    if summary.get("evidence") != TWIN_EVIDENCE:
        raise ForensicEvidenceError("Source Twin must retain its exact NO_FORGE_PARITY label")
    cases=summary.get("scenarios",[])
    if len(cases)!=1 or cases[0]["id"] != SCENE or cases[0]["simulated_ticks"]!=REAL_TICK_COUNT \
            or cases[0]["active_aircraft"]!=5 \
            or cases[0]["unique_aircraft_types"]!=3:
        raise ForensicEvidenceError("SOURCE Twin must be exact separate five-plane 340tick scenario")
    groups: dict[str,list[dict]]={u:[] for u in UNITS}
    for row in payload["slices"]:
        unit=row["unit_id"]
        if unit not in groups:
            raise ForensicEvidenceError("Unexpected simulated aircraft in original real twin case")
        groups[unit].append(row)
    for unit in UNITS:
        rows=sorted(groups[unit],key=lambda s:s["tick"])
        if [r["tick"] for r in rows] != list(range(REAL_TICK_COUNT+1)):
            raise ForensicEvidenceError(
                f"SOURCE Twin {unit} needs traceStride=1 and all tick 0..340")
        if rows[0]["maneuver"]!="INITIAL":
            raise ForensicEvidenceError("Simulated t0 must be preserved")
        groups[unit]=rows
    wanted={
        "b17":(0.0,165.0,0.0,0,"warfare_wings:b17"),
        "escort-left":(-48.0,172.0,18.0,0,"warfare_wings:p47n"),
        "escort-right":(48.0,172.0,18.0,0,"warfare_wings:p47n"),
        "raider-1":(-40.0,168.0,148.0,180,"warfare_wings:a6m"),
        "raider-2":(40.0,168.0,153.0,180,"warfare_wings:a6m"),
    }
    for unit,(x,y,z,yaw,typ) in wanted.items():
        row=groups[unit][0]
        if (row["x"],row["y"],row["z"],row["yaw_deg"],row["aircraft_id"]) != (
                x,y,z,float(yaw),typ):
            raise ForensicEvidenceError(f"SOURCE original Forge start geometry modified for {unit}")
    meta={"source_schema":summary["schema"],"evidence":summary["evidence"],
          "wind":summary["wind"],"sensor":summary["sensor"],"seed":summary["seed"],
          "source_scenario_gate":cases[0]["status"],
          "sha256_by_source_generated_filename":dict(sorted({
              filename:_sha(output/filename) for filename in (
                  "twin_summary.json","twin_units.csv","twin_pairs.csv",
                  "twin_assets.csv","twin_time_slices.csv","twin_sensor_events.csv")
          }.items()))}
    return payload,groups,meta


def _summary_stats(values: list[float]) -> dict:
    return {"min":round(min(values),9),
            "max":round(max(values),9),
            "mean":round(statistics.fmean(values),9),
            "rmse":round(math.sqrt(statistics.fmean(v*v for v in values)),9)}


def _trace_speed(v: tuple[float,float,float]) -> float:
    return math.sqrt(sum(n*n for n in v))*20.0


def _positions(real: RealReceipts, source: dict[str,list[dict]], unit: str, tick: int
              ) -> tuple[tuple[float,float,float],tuple[float,float,float]]:
    return (_vec(real.traces[unit][tick],True,real.coordinate_anchor),
            _vec(source[unit][tick],False,real.coordinate_anchor))


def analyze(
        real: RealReceipts, source_payload: dict,
        source: dict[str,list[dict]], source_meta: dict
) -> tuple[dict,list[dict],list[dict],list[dict]]:
    """Produce factual per-tick geometry and separate interpretation layers."""
    comparisons: list[dict] = []
    ticks: list[dict] = []
    events: list[dict] = []
    previous = {}
    unit_accumulators = {
        unit: {"position_error":[], "speed_error":[],
               "yaw_error":[], "pitch_error":[],"x_control_error":[],
               "z_control_error":[],"throttle_error":[],"real_path":0.0,
               "source_path":0.0,"real_visible_ticks":0,
               "source_visible_ticks":0,"real_escort_phase_ticks":0,
               "source_stale_ticks":0,"real_safety_ticks":0,
               "source_safety_ticks":0,
               "real_maneuvers":{},"source_maneuvers":{}} for unit in UNITS
    }
    pair_gaps: dict[str,list[tuple[float,float]]] = {
        a+"|"+b:[] for i,a in enumerate(UNITS) for b in UNITS[i+1:]
    }
    for tick in range(REAL_TICK_COUNT+1):
        nearest_real = (float("inf"),None)
        nearest_source = (float("inf"),None)
        pair_closest_real=(float("inf"),None)
        pair_closest_source=(float("inf"),None)
        for i,a in enumerate(UNITS):
            for b in UNITS[i+1:]:
                pa,sa=_positions(real,source,a,tick)
                pb,sb=_positions(real,source,b,tick)
                dr,ds=_dist(pa,pb),_dist(sa,sb)
                pair_gaps[a+"|"+b].append((dr,ds))
                if dr<pair_closest_real[0]:
                    pair_closest_real=(dr,a+"|"+b)
                if ds<pair_closest_source[0]:
                    pair_closest_source=(ds,a+"|"+b)
                if a=="b17" and b.startswith("raider"):
                    if dr<nearest_real[0]: nearest_real=(dr,b)
                    if ds<nearest_source[0]:nearest_source=(ds,b)
        is_real_under95=nearest_real[0]<PROTECTION
        is_source_under95=nearest_source[0]<PROTECTION
        is_real_inside_or_edge=nearest_real[0]<=PROTECTION
        is_source_inside_or_edge=nearest_source[0]<=PROTECTION
        frame={"schema":RECONCILIATION_SCHEMA,"tick":tick,
               "seconds":round(tick/20,4),
               "real_game_time":real.game_time_zero+tick,
               "real_forge_nearest_b17_threat_blocks":round(nearest_real[0],9),
               "real_forge_nearest_raider":nearest_real[1],
               "source_twin_nearest_b17_threat_blocks":round(nearest_source[0],9),
               "source_twin_nearest_raider":nearest_source[1],
               "delta_source_minus_real_threat_blocks":
                   round(nearest_source[0]-nearest_real[0],9),
               "real_forge_under95_strict":is_real_under95,
               "source_twin_under95_strict":is_source_under95,
               "real_forge_inside_or_touch_95":is_real_inside_or_edge,
               "source_twin_inside_or_touch_95":is_source_inside_or_edge,
               "real_forge_min_pair_blocks":round(pair_closest_real[0],9),
               "real_forge_min_pair_id":pair_closest_real[1],
               "source_twin_min_pair_blocks":round(pair_closest_source[0],9),
               "source_twin_min_pair_id":pair_closest_source[1],
               "real_forge_any_pair_lt6":pair_closest_real[0]<BODY,
               "source_twin_any_pair_lt6":pair_closest_source[0]<BODY,
               "tick_explanation":(
                   f"REAL Forge tick {tick} B17 nearest enemy "
                   f"{nearest_real[1]}={nearest_real[0]:.3f}b "
                   f"({'INSIDE' if is_real_inside_or_edge else 'OUTSIDE'} 95b). "
                   f"Autonomous SOURCE Twin nearest enemy "
                   f"{nearest_source[1]}={nearest_source[0]:.3f}b "
                   f"({'INSIDE' if is_source_inside_or_edge else 'OUTSIDE'} 95b); "
                   f"difference={nearest_source[0]-nearest_real[0]:+.3f}b. "
                   f"REAL closest aircraft pair {pair_closest_real[1]} "
                   f"{pair_closest_real[0]:.3f}b; "
                   f"SOURCE closest centre pair {pair_closest_source[1]} "
                   f"{pair_closest_source[0]:.3f}b. "
                   "This compares two autonomous decision loops, not shared-command "
                   "teacher forcing or Minecraft collision parity.")}
        ticks.append(frame)
        for prefix, inside, dist, origin_kind in (
                ("REAL_FORGE",is_real_inside_or_edge,nearest_real[0],"independent real geometries"),
                ("SOURCE_TWIN",is_source_inside_or_edge,nearest_source[0],"source centre positions")):
            previous_inside=previous.get(prefix+"_95",False)
            if tick>0 and inside != previous_inside:
                kind="B17_95_ENTER" if inside else "B17_95_EXIT"
                events.append({"tick":tick,"seconds":round(tick/20,4),
                               "channel":prefix,"unit_id":"b17","event":kind,
                               "severity":"critical" if inside else "info",
                               "details":f"{prefix} {'entered/touched' if inside else 'exited'} "
                                         f"the unchanged 95b B17 boundary, "
                                         f"nearest raider centre {dist:.3f}b; "
                                         f"computed from {origin_kind}; "
                                         f"real GameTest gate uses <95b, SOURCE uses <=95b"})
            previous[prefix+"_95"]=inside
        for prefix, danger, dist in (
                ("REAL_FORGE",pair_closest_real[0]<BODY,pair_closest_real[0]),
                ("SOURCE_TWIN",pair_closest_source[0]<BODY,pair_closest_source[0])):
            if tick>0 and danger != previous.get(prefix+"_6",False):
                events.append({"tick":tick,"seconds":round(tick/20,4),
                               "channel":prefix,"unit_id":"all","event":
                               "BODY_LT6_ENTER" if danger else "BODY_LT6_EXIT",
                               "severity":"critical" if danger else "info",
                               "details":f"{prefix} all-pair minimum = {dist:.3f}b; "
                                         "flight centres only, 6b gate"})
            previous[prefix+"_6"]=danger

        for unit in UNITS:
            r,s=real.traces[unit][tick],source[unit][tick]
            rp,sp=_positions(real,source,unit,tick)
            real_reason=_real_reason(r)
            speed_real=_trace_speed(r["velocity"])
            speed_source=_finite(s["speed_bps"],f"SOURCE {unit}@{tick}/speed")
            err=_dist(rp,sp)
            yaw_err=abs(_angle_diff(_finite(r["yaw_deg"],"real yaw"),s["yaw_deg"]))
            pitch_err=abs(_angle_diff(_finite(r["pitch_deg"],"real pitch"),s["pitch_deg"]))
            c_real=tuple(_finite(r[k],f"REAL {unit}@{tick}/{k}") for k in
                         ("command_x","command_z","command_throttle"))
            c_source=(s["control_x"],s["control_z"],s["control_throttle"])
            control_errors=tuple(abs(c_real[i]-c_source[i]) for i in range(3))
            real_seen=real_reason["sighting"]=="VISIBLE_UUID"
            source_seen=int(s["visible_hostiles_count"])>0
            source_track=int(s["stale_tracks_count"])>0
            summary=unit_accumulators[unit]
            summary["position_error"].append(err)
            summary["speed_error"].append(speed_source-speed_real)
            summary["yaw_error"].append(yaw_err)
            summary["pitch_error"].append(pitch_err)
            for name,value in zip(("x_control_error","z_control_error","throttle_error"),
                                  control_errors):
                if tick>0:summary[name].append(value)
            if tick>0:
                rprev,_=_positions(real,source,unit,tick-1)
                _,sprev=_positions(real,source,unit,tick-1)
                summary["real_path"]+=_dist(rprev,rp)
                summary["source_path"]+=_dist(sprev,sp)
                summary["real_visible_ticks"]+=int(real_seen)
                summary["source_visible_ticks"]+=int(source_seen)
                summary["source_stale_ticks"]+=int(source_track)
                summary["real_escort_phase_ticks"]+=int(
                    real_reason["phase"]=="ESCORT_COVER")
                summary["real_safety_ticks"]+=int(
                    r["world_safety_reason"] not in ("CLEAR","INITIAL"))
                summary["source_safety_ticks"]+=int(
                    s["safety_reason"] not in ("CLEAR","INITIAL"))
                for category,maneuver in (("real_maneuvers",r["maneuver"]),
                                          ("source_maneuvers",s["maneuver"])):
                    histogram=summary[category]
                    histogram[maneuver]=histogram.get(maneuver,0)+1
            comparisons.append({
                "schema":RECONCILIATION_SCHEMA,"tick":tick,
                "seconds":round(tick/20,4),"unit_id":unit,
                "aircraft_id":r["aircraft_id"],
                "real_evidence":"REAL_FORGE_VERIFIED_CSV",
                "source_evidence":"SOURCE_MICROKERNEL_NO_FORGE_PARITY",
                "real_game_time":r["game_time"],
                "real_x_aligned":round(rp[0],9),"real_y":round(rp[1],9),
                "real_z_aligned":round(rp[2],9),
                "source_x":round(sp[0],9),"source_y":round(sp[1],9),
                "source_z":round(sp[2],9),
                "combined_position_delta_blocks":round(err,9),
                "real_speed_bps":round(speed_real,9),
                "source_speed_bps":round(speed_source,9),
                "source_minus_real_speed_bps":round(speed_source-speed_real,9),
                "real_yaw_deg":_finite(r["yaw_deg"],"real yaw"),
                "source_yaw_deg":s["yaw_deg"],
                "abs_yaw_delta_deg":round(yaw_err,9),
                "real_pitch_deg":_finite(r["pitch_deg"],"real pitch"),
                "source_pitch_deg":s["pitch_deg"],
                "abs_pitch_delta_deg":round(pitch_err,9),
                "real_engine_power":_finite(r["engine_power"],"real spool"),
                "source_engine_power":s["engine_power"],
                "real_control_x":c_real[0],
                "source_control_x":c_source[0],
                "real_control_z":c_real[1],
                "source_control_z":c_source[1],
                "real_control_throttle":c_real[2],
                "source_control_throttle":c_source[2],
                "source_applied_control_x":s["applied_control_x"],
                "source_applied_control_z":s["applied_control_z"],
                "source_applied_control_throttle":s["applied_control_throttle"],
                "source_applied_control_from_policy_tick":
                    s["applied_control_from_policy_tick"],
                "source_command_generated_at_end_tick":
                    s["command_generated_at_end_tick"],
                "real_sighting":real_reason["sighting"],
                "real_sighting_raw":real_reason["sighting_raw"],
                "source_seen_now":source_seen,
                "source_remembered_stale":source_track,
                "source_contact_age_ticks":s["contact_age_ticks"],
                "source_contact_id":s["observed_contact_id"],
                "real_phase":real_reason["phase"],
                "real_phase_reason":real_reason["phase_reason"],
                "source_inferred_phase":_source_phase_estimate(s),
                "real_maneuver":r["maneuver"],
                "source_maneuver":s["maneuver"],
                "real_reason_code":real_reason["reason_code"],
                "source_reason_code":s["reason_code"],
                "real_world_safety":r["world_safety_reason"],
                "source_world_safety":s["safety_reason"],
                "real_nearest_b17_threat":round(nearest_real[0],9),
                "source_nearest_b17_threat":round(nearest_source[0],9),
                "real_b17_inside_or_touch95":is_real_inside_or_edge,
                "source_b17_inside_or_touch95":is_source_inside_or_edge,
                "real_global_min_pair_blocks":round(pair_closest_real[0],9),
                "source_global_min_pair_blocks":round(pair_closest_source[0],9),
                "unit_tick_explanation":(
                    f"At tick {tick}, REAL Forge {unit} reports phase "
                    f"{real_reason['phase']} ({real_reason['phase_reason']}), "
                    f"sighting {real_reason['sighting']}, maneuver {r['maneuver']} "
                    f"and stick x/z/throttle="
                    f"{c_real[0]:+.3f}/{c_real[1]:+.3f}/{c_real[2]:.3f}. "
                    f"The independent SOURCE Twin sees "
                    f"{int(s['visible_hostiles_count'])} opponents, keeps "
                    f"{int(s['stale_tracks_count'])} stale tracks, chooses "
                    f"{s['maneuver']} and stick "
                    f"{c_source[0]:+.3f}/{c_source[1]:+.3f}/{c_source[2]:.3f}. "
                    f"At the just-finished physics step, Twin ACTUALLY APPLIED "
                    f"{s['applied_control_x'] if s['applied_control_x'] is not None else 'NONE'}/"
                    f"{s['applied_control_z'] if s['applied_control_z'] is not None else 'NONE'}/"
                    f"{s['applied_control_throttle'] if s['applied_control_throttle'] is not None else 'NONE'} "
                    f"from prior policy tick {s['applied_control_from_policy_tick']}. "
                    f"Aligned 3D position separation is {err:.3f} blocks. "
                    "Different controller inputs/observations confound direct physics attribution."),
                "causal_note":("COMBINED_POLICY_SENSOR_WORLD_AND_PHYSICS_DIVERGENCE;"
                               "NOT_A_TEACHER_FORCED_PARITY_MEASUREMENT")
            })
            prev_key=unit
            if tick>0:
                checks=[
                    ("REAL_FORGE","REAL_SIGHTING_CHANGE",real_reason["sighting"],
                     "real sighting observation "+real_reason["sighting_raw"],"info"),
                    ("REAL_FORGE","REAL_PHASE_CHANGE",real_reason["phase"],
                     "original GameTest phase "+real_reason["phase"]+" / "+
                     real_reason["phase_reason"],"info"),
                    ("REAL_FORGE","REAL_MANEUVER_CHANGE",r["maneuver"],
                     "original runtime maneuver "+r["maneuver"]+
                     " (controller reason "+real_reason["reason_code"]+")","info"),
                    ("SOURCE_TWIN","TWIN_VISIBILITY_CHANGE",source_seen,
                     "synthetic observer currently "+("SEES" if source_seen else "DOES_NOT_SEE")+
                     " opponent; stale="+str(source_track),"info"),
                    ("SOURCE_TWIN","TWIN_MANEUVER_CHANGE",s["maneuver"],
                     "SOURCE policy maneuver "+s["maneuver"]+
                     " (reason "+s["reason_code"]+")","info"),
                    ("SOURCE_TWIN","TWIN_SAFETY_CHANGE",s["safety_reason"],
                     "SOURCE safety "+s["safety_reason"],"info")
                ]
                for channel,kind,value,detail,severity in checks:
                    key=(prev_key,kind)
                    if previous.get(key) != value:
                        events.append({"tick":tick,"seconds":round(tick/20,4),
                                       "channel":channel,"unit_id":unit,
                                       "event":kind,"severity":severity,
                                       "details":detail})
                    previous[key]=value
            else:
                previous[(prev_key,"REAL_SIGHTING_CHANGE")]=real_reason["sighting"]
                previous[(prev_key,"REAL_PHASE_CHANGE")]=real_reason["phase"]
                previous[(prev_key,"REAL_MANEUVER_CHANGE")]=r["maneuver"]
                previous[(prev_key,"TWIN_VISIBILITY_CHANGE")]=source_seen
                previous[(prev_key,"TWIN_MANEUVER_CHANGE")]=s["maneuver"]
                previous[(prev_key,"TWIN_SAFETY_CHANGE")]=s["safety_reason"]

    # Verify the complete per-frame geometry-derived REAL gate exactly matches
    # the independently loaded original acceptance sidecar. Never replace it
    # with the SOURCE scenario's own protection outcome.
    actual_real_intrusions=sum(t["real_forge_under95_strict"] for t in ticks)
    stored_real=real.sidecar["protected_assets"][0]
    closest_real=min(t["real_forge_nearest_b17_threat_blocks"] for t in ticks)
    if (actual_real_intrusions!=stored_real["hostile_inside_95_blocks_ticks"]
            or abs(closest_real-stored_real["closest_hostile_blocks"])>2e-6):
        raise ForensicEvidenceError("REAL 95b metric cannot be independently reconstructed")
    compared_pairs=[]
    for pair,samples in pair_gaps.items():
        a,b=pair.split("|")
        minima_real=min(sample[0] for sample in samples)
        minima_source=min(sample[1] for sample in samples)
        infringements_real=sum(x[0]<BODY for x in samples)
        infringements_source=sum(x[1]<BODY for x in samples)
        reference=next((pair for pair in real.sidecar["pairs"]
                        if {pair["a"],pair["b"]}=={a,b}),None)
        if (reference is None or abs(minima_real-reference["closest_blocks"])>2e-6
                or infringements_real!=reference["under_6_blocks_ticks"]):
            raise ForensicEvidenceError(f"Real original 6b pair evidence mismatch: {a}|{b}")
        compared_pairs.append({"first_unit":a,"second_unit":b,
            "real_forge_min_sampled_blocks":round(minima_real,9),
            "source_twin_min_sampled_blocks":round(minima_source,9),
            "real_forge_first_min_tick":next(
                i for i,x in enumerate(samples) if x[0]==minima_real),
            "source_twin_first_min_tick":next(
                i for i,x in enumerate(samples) if x[1]==minima_source),
            "real_forge_sampled_lt6_ticks":infringements_real,
            "source_twin_sampled_lt6_ticks":infringements_source})

    units=[]
    for unit in UNITS:
        observed=unit_accumulators[unit]
        rmse_pos=math.sqrt(statistics.fmean(p*p for p in observed["position_error"]))
        units.append({
            "unit_id":unit,"aircraft_id":real.traces[unit][0]["aircraft_id"],
            "real_path_blocks":round(observed["real_path"],9),
            "source_path_blocks":round(observed["source_path"],9),
            "final_position_error_blocks":round(observed["position_error"][-1],9),
            "mean_position_error_blocks":round(
                statistics.fmean(observed["position_error"]),9),
            "rmse_position_error_blocks":round(rmse_pos,9),
            "max_position_error_blocks":round(max(observed["position_error"]),9),
            "mean_abs_speed_error_bps":round(
                statistics.fmean(abs(x) for x in observed["speed_error"]),9),
            "max_abs_yaw_error_deg":round(max(observed["yaw_error"]),9),
            "max_abs_pitch_error_deg":round(max(observed["pitch_error"]),9),
            "mean_abs_control_x_error":round(
                statistics.fmean(observed["x_control_error"]),9),
            "mean_abs_control_z_error":round(
                statistics.fmean(observed["z_control_error"]),9),
            "mean_abs_throttle_error":round(
                statistics.fmean(observed["throttle_error"]),9),
            "real_sighting_visible_ticks":observed["real_visible_ticks"],
            "source_visible_ticks":observed["source_visible_ticks"],
            "source_stale_memory_ticks":observed["source_stale_ticks"],
            "real_escort_cover_phase_ticks":observed["real_escort_phase_ticks"],
            "real_world_safety_override_ticks":observed["real_safety_ticks"],
            "source_world_safety_override_ticks":observed["source_safety_ticks"],
            "real_maneuver_histogram":dict(sorted(observed["real_maneuvers"].items())),
            "source_maneuver_histogram":dict(sorted(observed["source_maneuvers"].items())),
        })

    twin_case=source_payload["summary"]["scenarios"][0]
    twin_asset=next(a for a in source_payload["assets"] if a["asset_unit"]=="b17")
    direct_source_inside=sum(t["source_twin_inside_or_touch_95"] for t in ticks[1:])
    if (direct_source_inside!=int(twin_asset["within95_sampled_ticks"])
            or round(min(t["source_twin_nearest_b17_threat_blocks"] for t in ticks),6)
                 !=round(twin_asset["min_sampled_hostile_blocks"],6)):
        raise ForensicEvidenceError("SOURCE twin 95b diagnostic does not match own trajectory")
    result={
        "schema":RECONCILIATION_SCHEMA,
        "comparison":"REAL_FORGE_ACCEPTANCE_VS_AUTONOMOUS_SOURCE_TWIN_20HZ",
        "real_evidence":{
            "class":FORGE_EVIDENCE,"schema":real.sidecar["schema_version"],
            "source":FORGE_SOURCE,"scenario":REAL_SCENE,
            "independent_acceptance":real.sidecar["conclusion"],
            "original_340tick_summary":real.sidecar,
            "saved_sidecar_verification":real.saved_sidecar_status,
            "accepted_results_from":
                "INDEPENDENT_VERIFIER_REAL_CONTROL_CSV_RECOMPUTATION_ONLY",
            "source_receipt_directory_label":real.root.name,
            "sha256_by_original_readonly_filename":dict(sorted(real.sha256.items())),
            "control_rows_per_aircraft":REAL_TICK_COUNT+1,
            "independent_geometry_sample_count":len(real.geometry),
            "independent_geometry_extra_post_control_samples":real.geometry_extra_sample,
            "excluded_post_control_stale_units":
                list(real.excluded_post_control_stale_units),
            "real_game_time_zero":real.game_time_zero,
            "original_real_world_base_xz_offset":{
                "x":real.coordinate_anchor[0],"z":real.coordinate_anchor[2]},
        },
        "source_twin_evidence":{
            **source_meta,"case_summary":twin_case,
            "source_b17_asset":twin_asset,
        },
        "comparison_contract":{
            "ticks_compared":REAL_TICK_COUNT+1,
            "tick_rate_hz":20,
            "body_separation_blocks":BODY,"b17_protection_blocks":PROTECTION,
            "real_game_test_acceptance_inside_rule":"distance<95",
            "source_twin_asset_inside_rule":"distance<=95",
            "entering_boundary_event_rule":"distance<=95",
            "real_position_alignment":"subtract original REAL B17 tick0 X,Z only; keep Y",
            "real_geometry_tick_mapping":"twin/controls sim_tick t ↔ original geometry sample t for 1..340; sample341 is independent extra",
            "not_teacher_forced":True,
            "source_actuation_phase":source_payload["summary"].get("actuation_phase"),
            "position_differences_conflate":["sensor/FOV/LOS","policy and role stages",
                                           "world collision geometry","physics and tick integration"],
            "source_cannot_prove_real_gates":True,
        },
        "aggregate":{
            "real_forge_min_b17_raider_blocks":round(closest_real,9),
            "source_twin_min_b17_raider_blocks":
                round(min(x["source_twin_nearest_b17_threat_blocks"] for x in ticks),9),
            "real_forge_strict_inside_95_ticks":actual_real_intrusions,
            "source_twin_strict_inside_95_ticks":
                sum(t["source_twin_under95_strict"] for t in ticks),
            "real_forge_inside_or_touch_95_ticks":
                sum(t["real_forge_inside_or_touch_95"] for t in ticks),
            "source_twin_inside_or_touch_95_ticks":
                sum(t["source_twin_inside_or_touch_95"] for t in ticks),
            "source_twin_swept_inside_95_ticks":int(twin_asset["within95_swept_ticks"]),
            "real_forge_min_sampled_body_blocks":
                round(min(p["real_forge_min_sampled_blocks"] for p in compared_pairs),9),
            "source_twin_min_sampled_body_blocks":
                round(min(p["source_twin_min_sampled_blocks"] for p in compared_pairs),9),
            "real_forge_sampled_lt6_pair_ticks":
                sum(p["real_forge_sampled_lt6_ticks"] for p in compared_pairs),
            "source_twin_sampled_lt6_pair_ticks":
                sum(p["source_twin_sampled_lt6_ticks"] for p in compared_pairs),
            "source_twin_swept_lt6_pair_ticks":
                twin_case["swept_lt6_pair_ticks"],
            "real_protection_failed":actual_real_intrusions>0,
            "source_protection_failed":twin_asset["protection_gate"]=="FAILED",
            "comparison_is_real_parity_gate":"NOT_A_PARITY_VERDICT",
            "top_position_divergence_unit":max(
                units,key=lambda u:u["final_position_error_blocks"])["unit_id"],
        },
        "units":units,"pairs":compared_pairs,
        "event_count":len(events),
    }
    return result,ticks,comparisons,sorted(events,key=lambda e:(
        e["tick"],e["channel"],e["unit_id"],e["event"]))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ForensicEvidenceError(f"Refuse to write empty forensic data to {path.name}")
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader()
        for row in rows:
            serializable={k:(json.dumps(v,ensure_ascii=False,sort_keys=True,
                                        separators=(",",":")) if isinstance(v,(dict,list))
                              else v) for k,v in row.items()}
            writer.writerow(serializable)


def _row_at(comparisons: list[dict],tick: int,unit: str) -> dict:
    return next(row for row in comparisons if row["tick"]==tick and row["unit_id"]==unit)


def _find_first(frames: list[dict],key: str) -> int | None:
    return next((row["tick"] for row in frames if row[key]),None)


def _markdown_report(result: dict,ticks: list[dict],
                     comparisons: list[dict],events: list[dict]) -> str:
    agg=result["aggregate"]
    first_real=_find_first(ticks,"real_forge_inside_or_touch_95")
    first_source=_find_first(ticks,"source_twin_inside_or_touch_95")
    real_min=min(ticks,key=lambda row:row["real_forge_nearest_b17_threat_blocks"])
    twin_min=min(ticks,key=lambda row:row["source_twin_nearest_b17_threat_blocks"])
    out=[
        "# Original real Forge B-17 / 340tick — closed-loop Twin forensic comparison",
        "",
        "**REAL evidence remains REAL; SOURCE Twin results are separate simulated observations.**",
        "The original GameTest outcome is recalculated independently from five pinned real "
        "Forge per-tick CSVs, checked against the saved real acceptance JSON, and cross-checked "
        "with the independent geometry CSV. This report does not reclassify that outcome.",
        "",
        "## Evidence identities",
        "",
        f"- **REAL**: {result['real_evidence']['class']}, "
        f"341 synchronized controller rows per aircraft across 340 updates; "
        f"accepted {result['real_evidence']['original_340tick_summary']['schema_version']} "
        f"(computed status **{result['real_evidence']['independent_acceptance']}**).",
        f"- **SOURCE**: {result['source_twin_evidence']['evidence']}; "
        "five independently piloted aircraft, pinned IA wind and per-airframe engine reactions.",
        "- Fixed 6-block body threshold; 95-block protectee threshold. REAL acceptance uses "
        "distance strictly below 95, Twin's source asset gate counts touch/inside 95.",
        "- Real X/Z coordinates are translated by the B-17's real tick-0 world X/Z origin "
        "(Y is retained) to compare the original relative GameTest start. The Twin starts "
        "from those same relative positions, initial yaw, velocity and mission assignments.",
        "- Every file's SHA-256 appears in the JSON under its own REAL or SOURCE evidence "
        "namespace; checksums identify bytes of local receipts, not a cryptographic "
        "endorsement by Mojang or an independent origin certificate.",
        "",
        "## Quantitative results",
        "",
        "| Metric | REAL Minecraft/Forge | SOURCE closed-loop Twin |",
        "|---|---:|---:|",
        f"| Minimum attacker to moving B-17 distance | "
        f"{agg['real_forge_min_b17_raider_blocks']:.3f} b | "
        f"{agg['source_twin_min_b17_raider_blocks']:.3f} b |",
        f"| Protected zone breaches (<95 b), 341 snapshots | "
        f"{agg['real_forge_strict_inside_95_ticks']} | "
        f"{agg['source_twin_strict_inside_95_ticks']} |",
        f"| Zone occupancy (<=95 b), 341 snapshots | "
        f"{agg['real_forge_inside_or_touch_95_ticks']} | "
        f"{agg['source_twin_inside_or_touch_95_ticks']} |",
        f"| Minimum tick-sampled all-pair aircraft-centre distance | "
        f"{agg['real_forge_min_sampled_body_blocks']:.3f} b | "
        f"{agg['source_twin_min_sampled_body_blocks']:.3f} b |",
        f"| Pair under 6b ticks (all pairs) | "
        f"{agg['real_forge_sampled_lt6_pair_ticks']} | "
        f"{agg['source_twin_sampled_lt6_pair_ticks']} |",
        f"| 95b protection gate | "
        f"{'FAILED' if agg['real_protection_failed'] else 'PASS GEOMETRY ONLY'} | "
        f"{'FAILED SOURCE' if agg['source_protection_failed'] else 'PASS SOURCE ONLY'} |",
        "",
        f"First observed REAL B-17 95b entry: tick {first_real}; "
        f"first Twin entry: tick {first_source}.",
        f"Closest REAL attacker: tick {real_min['tick']}, "
        f"{real_min['real_forge_nearest_raider']} at "
        f"{real_min['real_forge_nearest_b17_threat_blocks']:.3f}b. "
        f"Closest SOURCE attacker: tick {twin_min['tick']}, "
        f"{twin_min['source_twin_nearest_raider']} at "
        f"{twin_min['source_twin_nearest_b17_threat_blocks']:.3f}b.",
        "",
        "## Five real aircraft vs five simulated aircraft",
        "",
        "| Unit | Real sighting ticks | Twin sighting ticks | "
        "Twin stale-track ticks | Position RMSE b | Final divergence b | "
        "Mean abs X-control difference |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for unit in result["units"]:
        out.append(
            f"| {unit['unit_id']} | {unit['real_sighting_visible_ticks']} | "
            f"{unit['source_visible_ticks']} | {unit['source_stale_memory_ticks']} | "
            f"{unit['rmse_position_error_blocks']:.3f} | "
            f"{unit['final_position_error_blocks']:.3f} | "
            f"{unit['mean_abs_control_x_error']:.3f} |")
    out.extend(["","## At the FIRST real 95b entry", ""])
    if first_real is not None:
        out.append(ticks[first_real]["tick_explanation"])
        out.append("")
        for unit in UNITS:
            row=_row_at(comparisons,first_real,unit)
            out.append(f"- **{unit}** — REAL phase {row['real_phase']}, "
                       f"real sighting {row['real_sighting']}, maneuver "
                       f"{row['real_maneuver']}; SOURCE inferred phase "
                       f"{row['source_inferred_phase']}, maneuver "
                       f"{row['source_maneuver']}, observed="
                       f"{row['source_seen_now']}, stale={row['source_remembered_stale']}; "
                       f"combined coordinate difference "
                       f"{row['combined_position_delta_blocks']:.3f}b.")
    out.extend(["",
        "## Observed event chronology (first 45 events + all 95b boundary transitions)",
        "",
        "The per-unit controls CSV also includes a human-readable explanation "
        "of every aircraft decision at all 341 ticks. The ticks CSV provides "
        "every one of the 341 B17 threat/separation explanations.",
        ""])
    chosen=events[:45]+[e for e in events[45:] if "B17_95" in e["event"]]
    seen=set()
    for event in chosen:
        key=(event["tick"],event["channel"],event["unit_id"],event["event"])
        if key in seen: continue
        seen.add(key)
        out.append(f"- t={event['tick']:3d} ({event['seconds']:.2f}s) "
                   f"**{event['channel']} {event['unit_id']} / {event['event']}**: "
                   f"{event['details']}")
    out.extend(["",
        "## Interpretation constraints",
        "",
        "- The original real B-17 GameTest had two P-47N escorts and two A6M "
        "raiders for 340 ticks. It is materially different from the earlier "
        "single-raider, 190-tick SOURCE-only demonstration.",
        "- REAL pilot traces supply the logged maneuver, phase, signed raw controls, "
        "velocity, and UUID-based sighting state; SOURCE Twin supplies its own "
        "per-observer FOV/LOS/track TTL and a derived stage label. A UUID sighting "
        "is never converted to a named target without matching identity evidence.",
        "- Twin sensor defaults match LiveAirSensor 240-block range and "
        "150-degree FULL cone (75-degree half-angle), but use sampled height-field "
        "LOS rather than Minecraft collider raycast and airframe bounding-box centres.",
        "- REAL GameTest is authoritative for its own failure. Twin cannot certify "
        "in-game escort success or exact physics parity. Neither controls nor actual "
        "terrain/chunk/contact behavior are teacher-forced identical, so position "
        "error represents combined, confounded divergence.",
        "- REAL geometry may have a 341st post-control snapshot after its 340-tick "
        "control horizon. Tick-matched comparisons use REAL control t0..340 "
        "and geometry samples t1..340; extra geometry samples are disclosed.",
        "- No projectile, ammunition, damage, kill, or historical combat outcome "
        "is inferred from geometric firing or escort cues.",
        "",
    ])
    return "\n".join(out)


def save_comparison(output: Path, report: dict,frames: list[dict],
                    controls: list[dict], events: list[dict]) -> None:
    output.mkdir(parents=True,exist_ok=True)
    (output/"forensic_b17_summary.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",newline="\n")
    _write_csv(output/"forensic_b17_ticks.csv",frames)
    _write_csv(output/"forensic_b17_controls.csv",controls)
    _write_csv(output/"forensic_b17_events.csv",events)
    _write_csv(output/"forensic_b17_units.csv",report["units"])
    _write_csv(output/"forensic_b17_pairs.csv",report["pairs"])
    (output/"forensic_b17_findings.md").write_text(
        _markdown_report(report,frames,controls,events),encoding="utf-8",newline="\n")


FORENSIC_HTML = r"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KNEEKURA — ORIGINAL REAL FORGE B-17 / SOURCE TWIN Forensics</title>
<style>
:root{color-scheme:dark;--bg:#0a121c;--panel:#111e2e;--edge:#273d50;--ink:#e8f3ff;--mute:#a4bacf;--real:#6ee1b8;--twin:#f6af70;--danger:#fb8387;--accent:#aabdfd}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1530px;margin:auto;padding:24px clamp(12px,3vw,34px) 80px}h1{font-size:clamp(1.6rem,3vw,2.5rem);margin:3px 0 5px;letter-spacing:-.035em}
h2{font-size:1.04rem;margin:0 0 9px}h3{font-size:.95rem;margin:0 0 6px}
header{display:flex;gap:20px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap}
.eyebrow{color:var(--accent);font-size:.77rem;font-weight:800;letter-spacing:.16em}
.note{max-width:520px;padding:12px 15px;background:#252331;border-left:3px solid var(--danger);color:#f4d0cb}
p{color:var(--mute);margin:5px 0}.metrics{margin:22px 0 12px;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:9px}
.metric,.panel{border:1px solid var(--edge);border-radius:11px;background:var(--panel);padding:14px;min-width:0}
.metric strong{display:block;font-size:clamp(1.02rem,1.45vw,1.5rem);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.metric small{color:var(--mute)}.real{color:var(--real)}.twin{color:var(--twin)}.danger{color:var(--danger)}
.toolbar{display:flex;align-items:end;gap:14px;flex-wrap:wrap;margin:12px 0}
label{display:block;font-size:.83rem;color:var(--mute)}input,select{display:block;margin-top:5px;background:#152f43;border:1px solid #476176;border-radius:8px;color:var(--ink);padding:8px;font:inherit}
input[type=range]{padding:0;width:min(380px,75vw);accent-color:var(--accent)}
.stats{display:grid;grid-template-columns:1.1fr 1fr;gap:12px}.canvas-stack{display:grid;gap:12px}
canvas{width:100%;height:auto;border:1px solid #1c3348;background:#081521;border-radius:8px;display:block}
.key{display:flex;gap:16px;flex-wrap:wrap;font-size:.8rem;color:var(--mute);margin:10px 0 0}
.key span:before{content:"";display:inline-block;vertical-align:middle;margin-right:6px;height:3px;width:18px;background:var(--real)}
.key .source:before{background:var(--twin);border-top:1px dashed #142433}.key .bound:before{background:var(--danger)}
.tables{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.overflow{overflow:auto;max-height:430px}table{width:100%;border-collapse:collapse;font-size:.81rem;font-variant-numeric:tabular-nums}
th{color:var(--mute);background:#172a3e;position:sticky;top:0}
th,td{padding:8px 11px;border-bottom:1px solid #2c4052;text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}tr:hover{background:#1a364a}.click{cursor:pointer}
.explain{font-size:.91rem;padding:12px;background:#142537;border:1px solid #30495e;border-radius:8px;color:#d9edf9;line-height:1.65}
.events{max-height:385px;overflow:auto;display:grid;gap:7px;padding-right:7px}
.event{display:block;text-align:left;background:#15283a;border:1px solid #354b5e;border-radius:8px;padding:9px 12px;color:var(--ink);cursor:pointer}
.event:hover{background:#1b3a50}.event strong{font-size:.83rem}.event small{display:block;color:var(--mute)}
.code{font:12px/1.6 ui-monospace,Consolas,monospace;overflow-wrap:anywhere;color:#bed8f2}
details{margin-top:20px;border-top:1px solid var(--edge);padding-top:12px;color:var(--mute)}
details summary{cursor:pointer;color:var(--ink)}
@media(max-width:1060px){.metrics{grid-template-columns:repeat(3,1fr)}.stats,.tables{grid-template-columns:1fr}}
@media(max-width:560px){.metrics{grid-template-columns:repeat(2,1fr)}}
</style></head><body><main>
<header><div>
<div class="eyebrow">KNEEKURA / WARFARE WINGS / EVIDENCE RECONCILIATION</div>
<h1>340-tick B-17 flight forensics</h1>
<p>5 REAL Forge aircraft vs 5 autonomous SOURCE Twin aircraft — 341 aligned observations, 20Hz.</p>
</div><div class="note"><strong>証拠は混同しない。</strong> REALは保存済みMinecraft GameTestの独立確認済みCSV。SOURCE Twinは物理・観測・AIを別々に再実行した研究予測や。両者の位置差は純粋な物理精度ではない。</div></header>
<section id="metrics" class="metrics"></section>
<div class="toolbar">
 <label>時刻 / tick<input id="tick" type="range" min="0" max="340" step="1" value="0"></label>
 <label>詳細を見る航空機<select id="unit"></select></label>
 <label>イベントフィルター<select id="filter">
  <option value="all">すべて</option><option value="REAL_FORGE">実機のみ</option>
  <option value="SOURCE_TWIN">Twinのみ</option><option value="B17_95">95b境界のみ</option>
 </select></label>
 <span id="timestamp" class="code"></span>
</div>
<div class="stats">
<section class="panel"><h2>最接近時刻と防衛ライン / 実機とTwinは独立</h2>
 <canvas id="threat" width="900" height="310" aria-label="REALとSOURCEのB17脅威距離推移、95b境界"></canvas>
 <div class="key"><span>REAL Minecraft nearest enemy</span><span class="source">SOURCE Twin nearest enemy</span><span class="bound">95 blocks</span></div>
</section>
<section class="panel"><h2>上面図 (X/Z)、全5機の移動軌跡</h2>
 <canvas id="routes" width="850" height="460" aria-label="REALとSOURCEの飛行軌跡と境界"></canvas>
 <div class="key"><span>REAL original (solid)</span><span class="source">SOURCE Twin (dashed)</span><span class="bound">現在の95b境界</span></div>
</section>
</div>
<div class="tables">
 <section class="panel"><h2>各機の比較 / 状態と操縦</h2>
   <div class="overflow"><table><thead><tr><th>機体</th><th>REAL速度</th><th>Twin速度</th><th>位置差b</th><th>REAL判断</th><th>Twin判断</th></tr></thead><tbody id="state-table"></tbody></table></div>
   <div id="explanation" class="explain" style="margin-top:12px"></div>
 </section>
 <section class="panel"><h2>発見、フェーズ、操縦変更と95b侵入</h2>
   <div id="events" class="events"></div>
 </section>
</div>
<section class="panel" style="margin-top:12px"><h2>各機の全340tick総計</h2>
 <div class="overflow"><table><thead><tr><th>機体</th><th>REAL sighting</th><th>Twin sighting</th><th>Twin memory</th><th>軌跡差RMSE b</th><th>最終差 b</th><th>平均操舵X差</th></tr></thead><tbody id="summary-table"></tbody></table></div>
</section>
<details><summary>証拠と比較の前提（必ず確認）</summary>
<p>REAL: original-root-receipts-20261011-preserved の GameTest 340tick、5機のop-*.csv、operational-b17-escort-geometry.csv、独立acceptance JSON。各controlで REAL schema/source/scenario/tickを検証。B17初期X/Zを差し引いて同じ局所座標系に揃え、Yはそのまま。</p>
<p>SOURCE: Ia133Microkernel.tickWithReaction + PinnedIa133WindWorld、LiveAirSensorの240b、FULL FOV 150°に揃えた探知角75°半角。ただし高さベースLOS、近接は機体中心+線形補間、チーム通信と6tick記憶は実験仮定。物理は実機地形・接触・ネットワーク・武装を再現した証拠ではない。</p>
<p>REAL acceptanceは敵との距離が95b未満で侵犯。Twin sourceの防衛判定は95b以下。図は<=95bを境界入域と表示し、JSONには厳密な&lt;95bと&lt;=95bを別記。</p>
<p>元のGameTestは B-17×1、P-47N護衛×2、A6M攻撃機×2。過去の4機・190tick Twinとは機体数・隊形・時間が違う。SOURCEの別条件結果でREAL検査を合格と認定することはできない。</p>
<p class="code">Read-only original real CSV | forensic_b17_summary.json | forensic_b17_ticks.csv | forensic_b17_controls.csv | forensic_b17_events.csv | forensic_b17_units.csv | forensic_b17_pairs.csv | forensic_b17_findings.md</p>
<p class="code" id="evidence"></p>
</details>
</main><script>
"use strict";
const DATA=__FORENSIC_DATA__,R=DATA.report,FR=DATA.frames,C=DATA.controls,EV=DATA.events;
const $=id=>document.getElementById(id),fmt=(v,k=1)=>Number(v).toFixed(k);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const UNITS=["b17","escort-left","escort-right","raider-1","raider-2"];
const byTick=new Map(),byUnit=new Map();
for(const r of C){if(!byTick.has(r.tick))byTick.set(r.tick,[]);byTick.get(r.tick).push(r);
  if(!byUnit.has(r.unit_id))byUnit.set(r.unit_id,[]);byUnit.get(r.unit_id).push(r);}
$("unit").innerHTML=UNITS.map(u=>'<option value="'+u+'">'+u+'</option>').join("");
$("unit").value="b17";
const A=R.aggregate,realPass=!A.real_protection_failed,sourcePass=!A.source_protection_failed;
const metrics=[
 [fmt(A.real_forge_min_b17_raider_blocks,3)+" b","REAL threat min","real"],
 [fmt(A.source_twin_min_b17_raider_blocks,3)+" b","SOURCE threat min","twin"],
 [String(A.real_forge_strict_inside_95_ticks),"REAL <95b tick","danger"],
 [String(A.source_twin_strict_inside_95_ticks),"SOURCE <95b tick","danger"],
 [fmt(A.real_forge_min_sampled_body_blocks,3)+" b","REAL pair minimum","real"],
 [fmt(A.source_twin_min_sampled_body_blocks,3)+" b","SOURCE pair minimum","twin"],
];
$("metrics").innerHTML=metrics.map(([v,n,k])=>'<div class="metric"><strong class="'+k+'">'+esc(v)+'</strong><small>'+esc(n)+'</small></div>').join("");
$("summary-table").innerHTML=R.units.map(u=>'<tr><td>'+esc(u.unit_id)+'</td><td>'+u.real_sighting_visible_ticks+
  '</td><td>'+u.source_visible_ticks+'</td><td>'+u.source_stale_memory_ticks+'</td><td>'+
  fmt(u.rmse_position_error_blocks,2)+'</td><td>'+fmt(u.final_position_error_blocks,2)+'</td><td>'+
  fmt(u.mean_abs_control_x_error,3)+'</td></tr>').join("");
$("evidence").textContent="REAL: "+R.real_evidence.class+" | SOURCE: "+R.source_twin_evidence.evidence+
  " | verifier="+R.real_evidence.schema+" | comparison="+R.schema;
function canvas(id){const c=$(id),ctx=c.getContext("2d");
  ctx.fillStyle="#081521";ctx.fillRect(0,0,c.width,c.height);
  ctx.lineWidth=1;ctx.strokeStyle="#20364a";
  for(let n=0;n<=5;n++){let x=44+(c.width-88)*n/5,y=38+(c.height-76)*n/5;
    ctx.beginPath();ctx.moveTo(x,30);ctx.lineTo(x,c.height-28);ctx.stroke();
    ctx.beginPath();ctx.moveTo(35,y);ctx.lineTo(c.width-28,y);ctx.stroke();}
  return [ctx,c.width,c.height];}
function plotThreat(tick){
 const [ctx,w,h]=canvas("threat"),pd=48;
 const mx=Math.max(120,...FR.map(x=>Math.max(x.real_forge_nearest_b17_threat_blocks,x.source_twin_nearest_b17_threat_blocks)));
 const x=t=>pd+(w-2*pd)*t/340,y=v=>h-pd-(h-pd*2)*v/mx;
 ctx.strokeStyle="#fb8387";ctx.setLineDash([8,6]);ctx.lineWidth=2;
 ctx.beginPath();ctx.moveTo(x(0),y(95));ctx.lineTo(x(340),y(95));ctx.stroke();ctx.setLineDash([]);
 for(const [field,color,dash] of [
   ["real_forge_nearest_b17_threat_blocks","#6ee1b8",[]],
   ["source_twin_nearest_b17_threat_blocks","#f6af70",[6,5]]
 ]){
   ctx.strokeStyle=color;ctx.setLineDash(dash);ctx.lineWidth=3;
   ctx.beginPath();FR.forEach((r,i)=>i?ctx.lineTo(x(r.tick),y(r[field])):ctx.moveTo(x(r.tick),y(r[field])));
   ctx.stroke();ctx.setLineDash([]);
   const row=FR[tick];ctx.fillStyle=color;ctx.beginPath();ctx.arc(x(tick),y(row[field]),5,0,Math.PI*2);ctx.fill();
 }
 ctx.strokeStyle="#d5e3f5";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x(tick),30);ctx.lineTo(x(tick),h-28);ctx.stroke();
 ctx.fillStyle="#c9dae9";ctx.font="15px ui-monospace,monospace";
 ctx.fillText("95b B17 defence line",pd+6,Math.max(18,y(95)-8));ctx.fillText("0",pd,h-10);
 ctx.fillText("340 ticks / 17s",w-pd-155,h-10);
}
function plotRoutes(tick){
 const [ctx,w,h]=canvas("routes"),pd=47,chosen=$("unit").value;
 let all=[];
 for(const u of UNITS)for(const r of byUnit.get(u))
   all.push([r.real_x_aligned,r.real_z_aligned],[r.source_x,r.source_z]);
 const minx=Math.min(...all.map(x=>x[0]))-95,maxx=Math.max(...all.map(x=>x[0]))+95;
 const minz=Math.min(...all.map(x=>x[1]))-95,maxz=Math.max(...all.map(x=>x[1]))+95;
 const scale=Math.min((w-2*pd)/(maxx-minx),(h-2*pd)/(maxz-minz));
 const px=x=>w/2+(x-(minx+maxx)/2)*scale;
 const py=z=>h/2-(z-(minz+maxz)/2)*scale;
 for(const kind of ["real","source"]){
  const bomber=byUnit.get("b17")[tick];
  const bx=kind==="real"?bomber.real_x_aligned:bomber.source_x;
  const bz=kind==="real"?bomber.real_z_aligned:bomber.source_z;
  ctx.strokeStyle=kind==="real"?"#6ee1b8":"#f6af70";
  ctx.setLineDash(kind==="real"?[7,5]:[3,7]);
  ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(px(bx),py(bz),95*scale,0,2*Math.PI);ctx.stroke();ctx.setLineDash([]);
 }
 const shades={"b17":"#fff3bc","escort-left":"#6ee1b8","escort-right":"#6ee1b8",
  "raider-1":"#f5a8b8","raider-2":"#f5a8b8"};
 for(const u of UNITS){
   const rows=byUnit.get(u).slice(0,tick+1);
   for(const kind of ["real","source"]){
     ctx.strokeStyle=kind==="real"?"#6ee1b8":"#f6af70";
     ctx.globalAlpha=u===chosen?1:.33;ctx.lineWidth=u===chosen?3.2:1.5;
     ctx.setLineDash(kind==="real"?[]:[5,5]);ctx.beginPath();
     rows.forEach((p,i)=>{
       const pos=kind==="real"?[p.real_x_aligned,p.real_z_aligned]:[p.source_x,p.source_z];
       i?ctx.lineTo(px(pos[0]),py(pos[1])):ctx.moveTo(px(pos[0]),py(pos[1]));
     });
     ctx.stroke();ctx.setLineDash([]);
     const end=rows[rows.length-1],pos=kind==="real"?
       [end.real_x_aligned,end.real_z_aligned]:[end.source_x,end.source_z];
     ctx.fillStyle=shades[u];ctx.beginPath();ctx.arc(px(pos[0]),py(pos[1]),u===chosen?6:3,0,2*Math.PI);ctx.fill();
     if(u===chosen){ctx.fillStyle="#e8f3ff";ctx.font="12px Consolas,monospace";
        ctx.fillText(u+" "+kind,px(pos[0])+7,py(pos[1])-7);}
     ctx.globalAlpha=1;
   }
 }
}
function renderEvents(){
 const filter=$("filter").value;
 const chosen=EV.filter(e=>filter==="all"||e.channel===filter||
    filter==="B17_95"&&e.event.startsWith("B17_95"));
 $("events").innerHTML=chosen.map(e=>'<button class="event" data-tick="'+e.tick+'"><strong>'+
  esc("t"+e.tick+" • "+e.channel+" • "+e.unit_id+" • "+e.event)+'</strong><small>'+
  esc(e.details)+'</small></button>').join("");
 $("events").querySelectorAll("button").forEach(btn=>btn.addEventListener("click",()=>{
   $("tick").value=Number(btn.dataset.tick);update();
 }));
}
function update(){
 const tick=Math.max(0,Math.min(340,Number($("tick").value))),u=$("unit").value;
 const frame=FR[tick],all=byTick.get(tick)||[],line=byUnit.get(u)[tick];
 $("timestamp").textContent="tick "+tick+" | "+fmt(tick/20,2)+"s | REAL game_time "+
   frame.real_game_time+" | REAL gate "+(realPass?"PASS":"FAILED")+
   " / SOURCE "+(sourcePass?"SOURCE PASS":"SOURCE FAILED");
 $("state-table").innerHTML=all.map(r=>'<tr class="click" data-unit="'+esc(r.unit_id)+'"><td>'+
   esc(r.unit_id)+'</td><td>'+fmt(r.real_speed_bps,2)+'</td><td>'+
   fmt(r.source_speed_bps,2)+'</td><td>'+fmt(r.combined_position_delta_blocks,2)+
   '</td><td>'+esc(r.real_maneuver)+'</td><td>'+esc(r.source_maneuver)+'</td></tr>').join("");
 $("state-table").querySelectorAll("tr").forEach(tr=>tr.addEventListener("click",()=>{
   $("unit").value=tr.dataset.unit;update();
 }));
 $("explanation").textContent=line.unit_tick_explanation+"\n"+frame.tick_explanation;
 plotThreat(tick);plotRoutes(tick);
}
$("tick").addEventListener("input",update);
$("unit").addEventListener("change",update);
$("filter").addEventListener("change",renderEvents);
const first=FR.find(r=>r.real_forge_inside_or_touch_95);
$("tick").value=first?first.tick:0;
renderEvents();update();
</script></body></html>
"""


def make_forensic_html(output: Path,report: dict,
                       frames: list[dict],controls: list[dict],events: list[dict]) -> Path:
    """Static file:// report, no runtime network fetch, with namespaced evidence."""
    payload={"report":report,"frames":frames,"controls":controls,"events":events}
    embedded=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(",",":"))
    embedded=(embedded.replace("<","\\u003c").replace(">","\\u003e")
              .replace("&","\\u0026").replace("\u2028","\\u2028")
              .replace("\u2029","\\u2029"))
    destination=output/"forensic_b17.html"
    destination.write_text(FORENSIC_HTML.replace("__FORENSIC_DATA__",embedded),
                           encoding="utf-8",newline="\n")
    return destination


def run_forensic(
        real_directory: Path, output: Path, *,
        manifest_path: Path = DEFAULT_MANIFEST,
        seed: int = 20261011, java_home: Path | None = None,
        reuse_twin: bool = False, reverse_roster: bool = False,
        quarantine_stale_sidecar: bool = False
) -> tuple[dict,list[dict],list[dict],list[dict]]:
    real_directory=real_directory.resolve()
    output=output.resolve()
    if output==real_directory or real_directory in output.parents \
            or output==manifest_path.resolve():
        raise ForensicEvidenceError(
            "Generated SOURCE/forensic outputs must never overwrite original REAL Forge receipts")
    verified_real=load_verified_real(
        real_directory,manifest_path,
        quarantine_stale_sidecar=quarantine_stale_sidecar)
    # Validate REAL provenance BEFORE creating any Twin data. Original file
    # access is read-only; all generated artifacts live under OUTPUT.
    if not reuse_twin:
        with tempfile.TemporaryDirectory(prefix="ww-b17-forensic-classes-") as directory:
            classes=Path(directory)
            javac,java=get_java17(java_home)
            compile_lab(javac,classes)
            run_twin(java,classes,output,seed=seed,unique_ticks=340,
                     trace_stride=1,scenario=SCENE,reverse_roster=reverse_roster)
    payload,traces,source_meta=load_source_twin(output)
    report,frames,controls,events=analyze(verified_real,payload,traces,source_meta)
    save_comparison(output,report,frames,controls,events)
    return report,frames,controls,events


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True,
                        help="Generated SOURCE twin and separately labelled forensic outputs")
    parser.add_argument("--real-dir",type=Path,default=DEFAULT_REAL,
                        help="Read-only ORIGINAL saved real Forge B17 root")
    parser.add_argument("--manifest",type=Path,default=DEFAULT_MANIFEST,
                        help="Tracked real Forge scenario identity manifest")
    parser.add_argument("--seed",type=int,default=20261011,
                        help="SOURCE deterministic seed; no effect on original REAL evidence")
    parser.add_argument("--java-home",type=Path)
    parser.add_argument("--reuse-twin",action="store_true",
                        help="Check previously generated full-resolution Twin CSV without running Java")
    parser.add_argument("--reverse-roster",action="store_true",
                        help="Check that changed Java internal aircraft order preserves outcome")
    parser.add_argument("--quarantine-stale-sidecar",action="store_true",
                        help="Explicitly study newer REAL pilot CSV with an obsolete archived"
                             " sidecar: independently recompute REAL acceptance, isolate the"
                             " mismatched sidecar as untrusted, and do NOT use its numbers")
    args=parser.parse_args()
    try:
        report,frames,controls,events=run_forensic(
            args.real_dir,args.output,manifest_path=args.manifest,seed=args.seed,
            java_home=args.java_home,reuse_twin=args.reuse_twin,
            reverse_roster=args.reverse_roster,
            quarantine_stale_sidecar=args.quarantine_stale_sidecar)
        # Inline file:// charts are built only after both evidence sources pass.
        make_forensic_html(args.output,report,frames,controls,events)
    except (OSError,ForensicEvidenceError,OperationalFailure,ValueError,
            KeyError,IndexError,AssertionError) as exc:
        print(f"B17_FORENSIC_EVIDENCE_REJECTED: {exc}",file=sys.stderr)
        raise SystemExit(2) from None
    summary=report["aggregate"]
    print("B17_FORENSIC_RECONCILIATION_COMPLETE; NOT_A_PHYSICS_PARITY_VERDICT")
    print("REAL_ORIGINAL_SAVED_SIDECAR_STATUS "
          +report["real_evidence"]["saved_sidecar_verification"])
    print(f"REAL_FORGE {report['real_evidence']['independent_acceptance']} "
          f"min_b17_threat={summary['real_forge_min_b17_raider_blocks']:.6f}b "
          f"strict_lt95_ticks={summary['real_forge_strict_inside_95_ticks']} "
          f"min_pair={summary['real_forge_min_sampled_body_blocks']:.6f}b")
    print(f"SOURCE_TWIN {report['source_twin_evidence']['source_scenario_gate']} "
          f"min_b17_threat={summary['source_twin_min_b17_raider_blocks']:.6f}b "
          f"strict_lt95_ticks={summary['source_twin_strict_inside_95_ticks']} "
          f"min_pair={summary['source_twin_min_sampled_body_blocks']:.6f}b")
    print(f"FORENSIC_EVIDENCE rows_tick={len(frames)} rows_unit={len(controls)} "
          f"events={len(events)}; REAL CSVs unchanged")


if __name__ == "__main__":
    main()

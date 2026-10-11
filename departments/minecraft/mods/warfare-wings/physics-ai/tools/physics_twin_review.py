#!/usr/bin/env python3
"""Independent original-Forge flight receipt vs offline source replay examiner.

Input twin CSVs are computed by Java from pinned airframe source models,
not by this verifier. This validator cross-checks EACH recorded position,
velocity, identity, world-clock tick and stated assumptions against the
separately saved original Forge GameTest receipt. A real GameTest execution
and pinned JAR hash check are still required as independent provenance.

The optional position threshold gates ONLY the sampled flight/controls
outside terrain collisions, weapons, damaged craft and unobserved changes.
The original B17 escort 95b mission gate is separate and never relaxed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path
from statistics import median

WW_OWNER_SHA = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
IA_SHA512 = "7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055"
NEUTRAL_SCHEMA = ("schema_version,source,scenario_id,aircraft_id,tick,game_time,"
                  "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,speed_bps,horizontal_speed_bps,"
                  "yaw_deg,pitch_deg,roll_deg,engine_target,engine_power,fuel_utilization,"
                  "raw_x,raw_y,raw_z,smooth_x,smooth_y,smooth_z")
TACTICAL_SCHEMA = ("schema_version,source,scenario_id,aircraft_id,sim_tick,game_time,"
                   "pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,yaw_deg,pitch_deg,"
                   "engine_target,engine_power,smooth_x,smooth_z,command_x,command_z,"
                   "command_throttle,maneuver,reason,world_safety_reason,terrain_clearance_blocks")

REPLAY_REQUIRED = (
    "scenario_id", "aircraft_id", "tick", "game_time", "real_pos_x", "real_pos_y", "real_pos_z",
    "real_vel_x", "real_vel_y", "real_vel_z", "one_step_pos_error_blocks",
    "one_step_vel_error_bpt", "one_step_yaw_error_deg", "one_step_pitch_error_deg",
    "one_step_engine_power_error", "one_step_smooth_x_error", "one_step_smooth_z_error",
    "free_run_pos_error_blocks", "free_run_vel_error_bpt", "free_run_speed_error_bps",
    "free_run_yaw_error_deg", "free_run_pitch_error_deg", "trace_kind", "assumptions",
)


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"{path.name}: invalid/duplicate CSV column names")
        content = list(reader)
    if not content or any(None in row or None in row.values() for row in content):
        raise ValueError(f"{path.name}: missing or ragged physics recording")
    return list(reader.fieldnames), content


def number(value: str, field: str, scenario: str, tick: int) -> float:
    try:
        actual = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{scenario} tick={tick}: {field} is nonnumeric") from exc
    if not math.isfinite(actual):
        raise ValueError(f"{scenario} tick={tick}: {field} is nonfinite")
    return actual


def _rmse(sequence: list[float]) -> float:
    return math.sqrt(sum(value * value for value in sequence) / len(sequence))


def analyze_one(twin: Path, original_dir: Path) -> tuple[dict, list[dict]]:
    header, replay = rows(twin)
    if not set(REPLAY_REQUIRED).issubset(header):
        raise ValueError(f"{twin.name}: missing mandatory independent residual fields")
    kind = replay[0]["trace_kind"]
    if kind not in ("neutral_pinned_wind", "tactical_pinned_wind"):
        raise ValueError(f"{twin.name}: source simulator omitted exact IA wind model")
    if not twin.name.endswith("-pinned-wind.csv"):
        raise ValueError(f"{twin.name}: incorrect paired replay filename")
    scenario = twin.name.removesuffix("-pinned-wind.csv")
    expected_assumptions = ("AIRBORNE_PINNED_IA_WIND|ENGINE_POWER_OBSERVED|ROLL_OBSERVED"
                            if kind == "neutral_pinned_wind" else
                            "AIRBORNE_PINNED_IA_WIND|RECORDED_NEXT_TICK_AXIS_COMMAND|"
                            "ROLL_UNOBSERVED|FUEL_ASSUMED_1|VOXEL_UNOBSERVED")
    actual_path = original_dir / (scenario + ("-throttle-step-v1-runtime.csv"
                                             if kind == "neutral_pinned_wind" else "-forge-controls.csv"))
    # Neutral twin filenames use just aircraft base ID, not scenario suffix.
    if kind == "neutral_pinned_wind":
        if not scenario.startswith("roster-"):
            original_path = original_dir / (scenario + "-throttle-step-v1-runtime.csv")
        else:
            raise ValueError("Neutral-source flight must use a real throttle experiment")
    else:
        original_path = actual_path
    actual_columns, actual = rows(original_path)
    expected_header = NEUTRAL_SCHEMA if kind == "neutral_pinned_wind" else TACTICAL_SCHEMA
    if ",".join(actual_columns) != expected_header:
        raise ValueError(f"{scenario}: original GameTest trace columns changed")
    real_source = "minecraft_runtime" if kind == "neutral_pinned_wind" else "minecraft_runtime_ia_next_tick_injection"
    real_schema = "ww.physics.trace.v1" if kind == "neutral_pinned_wind" else "ww.physics.forge-tactical-pilot.v1"
    if len(actual) != len(replay) + 1 or len(replay) < 3:
        raise ValueError(f"{scenario}: incomplete paired real-forge physics timeline")
    aircraft = replay[0]["aircraft_id"]
    if kind == "neutral_pinned_wind" and aircraft != "warfare_wings:" + scenario:
        raise ValueError(f"{scenario}: original aircraft identity is wrong")
    if kind == "tactical_pinned_wind" and scenario.startswith("roster-") and aircraft != "warfare_wings:" + scenario[7:]:
        raise ValueError(f"{scenario}: 24-aircraft smoke roster identity mismatch")
    if any(row["schema_version"] != real_schema or row["source"] != real_source
           or row["aircraft_id"] != aircraft for row in actual):
        raise ValueError(f"{scenario}: input is not an unchanged real Minecraft trace")
    if any(row["scenario_id"] != (scenario + "-throttle-step-v1"
                                    if kind == "neutral_pinned_wind" else scenario) for row in actual):
        raise ValueError(f"{scenario}: mixed or mislabeled GameTest evidence")
    elapsed_clock = int(actual[0]["game_time"])
    if int(actual[0]["tick" if kind == "neutral_pinned_wind" else "sim_tick"]) != 0:
        raise ValueError(f"{scenario}: original GameTest starts at an unexpected tick")

    one_pos, one_vel, yaw, pitch, free_pos, free_vel, free_yaw, engine, smooth_x = ([] for _ in range(9))
    series = []
    for index, (line, original) in enumerate(zip(replay, actual[1:]), start=1):
        real_tick_field = "tick" if kind == "neutral_pinned_wind" else "sim_tick"
        if int(original[real_tick_field]) != index or int(original["game_time"]) != elapsed_clock + index:
            raise ValueError(f"{scenario}: non-consecutive exact Forge entity clock at tick {index}")
        if (line["scenario_id"] != original["scenario_id"] or line["aircraft_id"] != aircraft
                or int(line["tick"]) != index or int(line["game_time"]) != elapsed_clock + index
                or line["trace_kind"] != kind or line["assumptions"] != expected_assumptions):
            raise ValueError(f"{scenario}: non-matching offline physical replay identity at tick {index}")
        for axis in "xyz":
            for group in ("pos", "vel"):
                if abs(number(line[f"real_{group}_{axis}"], group, scenario, index)
                       - number(original[f"{group}_{axis}"], group, scenario, index)) > 1e-8:
                    raise ValueError(f"{scenario}: original Minecraft state substituted at tick {index}")
        if kind == "tactical_pinned_wind":
            if line["one_step_roll_error_deg"] != "":
                raise ValueError(f"{scenario}: falsely asserted parity for unobserved tactical roll")
            if index > 1 and number(original["terrain_clearance_blocks"], "clearance", scenario, index) < 10:
                raise ValueError(f"{scenario}: voxel contact invalidates free-air matching assumptions")
        else:
            number(line["one_step_roll_error_deg"], "real roll", scenario, index)
        one_pos.append(number(line["one_step_pos_error_blocks"], "one-step pos", scenario, index))
        one_vel.append(number(line["one_step_vel_error_bpt"], "one-step velocity", scenario, index))
        yaw.append(number(line["one_step_yaw_error_deg"], "one-step yaw", scenario, index))
        pitch.append(number(line["one_step_pitch_error_deg"], "one-step pitch", scenario, index))
        free_pos.append(number(line["free_run_pos_error_blocks"], "free-run pos", scenario, index))
        free_vel.append(number(line["free_run_vel_error_bpt"], "free-run velocity", scenario, index))
        free_yaw.append(number(line["free_run_yaw_error_deg"], "free-run yaw", scenario, index))
        engine.append(number(line["one_step_engine_power_error"], "engine", scenario, index))
        smooth_x.append(number(line["one_step_smooth_x_error"], "smoothing", scenario, index))
        series.append({"tick": index, "free": free_pos[-1], "one": one_pos[-1],
                       "yaw": free_yaw[-1], "speed": number(line["free_run_speed_error_bps"],
                                                            "free-run speed", scenario, index)})
    return ({"scenario": scenario, "aircraft": aircraft,
             "kind": kind, "ticks": len(replay), "original_receipt_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
             "replay_sha256": hashlib.sha256(twin.read_bytes()).hexdigest(),
             "one_step_position_rmse_blocks": _rmse(one_pos),
             "one_step_velocity_rmse_bpt": _rmse(one_vel),
             "one_step_yaw_rmse_deg": _rmse(yaw), "one_step_pitch_rmse_deg": _rmse(pitch),
             "one_step_engine_rmse": _rmse(engine), "one_step_smooth_x_rmse": _rmse(smooth_x),
             "free_run_final_position_error_blocks": free_pos[-1],
             "free_run_max_position_error_blocks": max(free_pos),
             "free_run_final_velocity_error_bpt": free_vel[-1],
             "free_run_final_yaw_error_deg": free_yaw[-1],
             "roll_status": "OBSERVED" if kind == "neutral_pinned_wind" else "NOT_OBSERVED",
             "physics_scope": "ORIGINAL_JAR_MATCHED_RECORDED_FREE_AIR_CONTROLS_NOT_ALL_PHYSICS"}, series)


def verify(twin_dir: Path, original_dir: Path, output_dir: Path | None,
           expected_roster: int = 0, expected_neutral: int = 0,
           expected_tactical: int = 0, max_final_drift: float | None = None) -> dict:
    if max_final_drift is not None and (not math.isfinite(max_final_drift) or max_final_drift <= 0):
        raise ValueError("Invalid explicit matched-recording position threshold")
    traces = sorted(twin_dir.glob("*-pinned-wind.csv"))
    if not traces:
        raise ValueError("No original-physics replay traces supplied")
    details=[]
    series={}
    for path in traces:
        result, times = analyze_one(path,original_dir)
        details.append(result)
        series[result["scenario"]] = times
    roster = sum(c["scenario"].startswith("roster-") for c in details)
    neutral = sum(c["kind"] == "neutral_pinned_wind" for c in details)
    tactical = len(details) - neutral - roster
    if (expected_roster and roster != expected_roster
            or expected_neutral and neutral != expected_neutral
            or expected_tactical and tactical != expected_tactical):
        raise ValueError("Required actual full-airframe/neutral/tactical coverage incomplete: "
                         f"roster={roster} neutral={neutral} tactical={tactical}")
    failed=[]
    if max_final_drift is not None:
        failed=[f"UNMATCHED_FREE_AIR_TRAJECTORY:{row['scenario']}:"
                f"{row['free_run_final_position_error_blocks']:.9f}"
                for row in details if row["free_run_final_position_error_blocks"] > max_final_drift]
    conclusion=("RECORDED_FREE_AIR_PHYSICS_GATE_FAILED" if failed else
                "RECORDED_FREE_AIR_PHYSICS_GATE_PASSED_NOT_FULL_MINECRAFT_PARITY"
                if max_final_drift is not None else "MEASURED_DIAGNOSTICS_ONLY_NO_ACCEPTANCE_THRESHOLD")
    summary={
        "schema_version": "ww.physics.twin-original-jar-replay.v1",
        "source_exact_owner_ww_sha256": WW_OWNER_SHA,
        "source_pinned_ia_sha512": IA_SHA512,
        "replay_explanation": "Prerendered actual-Forge entity controls replayed in separate original-physics source without new AI decisions",
        "original_jar_binary_attestation": "MUST_COME_FROM_EXTERNAL_EXACT_FORGE_GAMETEST_AND_HASH_GATE",
        "real_aircraft": len({case["aircraft"] for case in details}),
        "cases": len(details), "paired_tick_samples": sum(case["ticks"] for case in details),
        "coverage": {"24_aircraft_sequential": roster, "neutral_401_samples": neutral,
                     "combat_or_strike_recorded_controls": tactical},
        "maximum_one_step_position_rmse_blocks": max(c["one_step_position_rmse_blocks"] for c in details),
        "maximum_free_run_final_position_error_blocks": max(c["free_run_final_position_error_blocks"] for c in details),
        "median_free_run_final_position_error_blocks": median(c["free_run_final_position_error_blocks"] for c in details),
        "scope_limits": ["recorded-control reproduction, NOT new AI decisions",
                         "flat airborne collision-free experiments only",
                         "terrain voxels, entity collision, water and crash damage NOT verified",
                         "weapons, projectile owner, friendly fire, kill attribution NOT verified",
                         "tactical roll/fuel unavailable in telemetry; assumptions explicitly labeled",
                         "real historical combat success is a separate acceptance gate"],
        "threshold_scope": "recorded free-air final position deviation, blocks, no operational B17 threshold adjustment",
        "max_final_drift_blocks_gate": max_final_drift,
        "failed_gates": failed, "conclusion": conclusion,
        "trace_metrics": details,
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True,exist_ok=True)
        (output_dir/"physics-twin-evidence.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        with (output_dir/"physics-twin-evidence.csv").open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(details[0]))
            writer.writeheader()
            writer.writerows(details)
        (output_dir/"physics-twin-explorer.html").write_text(_render_html(summary,series),encoding="utf-8")
    return summary


def _render_html(summary: dict, series: dict[str, list[dict]]) -> str:
    # No remote fonts, images, CDNs or DOM injection of untrusted trace names.
    embedded=json.dumps({"traces":summary["trace_metrics"],"series":series},separators=(",",":"),ensure_ascii=True)
    embedded=embedded.replace("<","\\u003c").replace(">","\\u003e")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Warfare Wings Flight Physics Twin — Original Forge vs Source</title><style>
:root{color-scheme:dark;--ink:#dce8f3;--muted:#93aac1;--line:#263e4e;--accent:#5dd39e;--blue:#7aa8f5}
body{margin:0;background:#0c1420;color:var(--ink);font:15px system-ui,Segoe UI,sans-serif}main{max-width:1130px;margin:0 auto;padding:30px 24px}
h1{font-size:29px;margin:0 0 8px}p{line-height:1.6;color:var(--muted)}h2{font-size:19px;margin-top:28px}
.eyebrow{color:var(--accent);font-size:12px;letter-spacing:2px;font-weight:700}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:13px}
.tile,.panel{background:#142232;border:1px solid var(--line);border-radius:12px;padding:18px}.tile b{display:block;font-size:24px;margin-top:6px;font-variant-numeric:tabular-nums}
.tile small,small{color:var(--muted)}.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
select{padding:9px 14px;background:#17283a;color:var(--ink);border:1px solid #476074;border-radius:8px;max-width:100%}
svg{width:100%;height:292px;background:#0d1827;border-radius:9px;display:block}svg text{fill:var(--muted);font-size:11px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:9px 11px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:600;position:sticky;top:0;background:#142232}tbody tr:hover{background:#203647}
.scroll{overflow:auto;max-height:390px}.legend{display:flex;gap:20px;color:var(--muted);font-size:13px;margin-top:10px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px}
footer{margin-top:30px;color:var(--muted);font-size:12px}code{color:#bee7d4}
</style></head><body><main><div class="eyebrow">KNEEKURA · FLIGHT PHYSICS TWIN</div>
<h1>Original Forge → deterministic flight physics replay</h1>
<p>Measured actual server aircraft positions against independent original-IA aerodynamic calculations. Real recorded pilot commands only; this does not simulate new hostile decisions, voxel collisions, weapons or completed missions.</p>
<section class="metrics"><div class="tile">Recorded flight cases<b id="cases"></b><small>Separate actual Minecraft receipts</small></div>
<div class="tile">Real-aircraft airframes<b id="types"></b><small>Unique original Warfare Wings aircraft</small></div>
<div class="tile">Paired 20Hz steps<b id="ticks"></b><small>Model result independently checked per tick</small></div>
<div class="tile">Largest final drift<b id="max"></b><small>Blocks, for recorded free-air controls</small></div></section>
<h2>Physics deviation by aircraft and mission</h2><div class="panel"><div class="controls"><label>Flight recording <select id="scene"></select></label>
<label>Residual <select id="metric"><option value="free">Accumulated position (blocks)</option><option value="one">One-step physical position (blocks)</option><option value="yaw">Accumulated yaw (degrees)</option><option value="speed">Accumulated speed (blocks/s)</option></select></label></div>
<svg viewBox="0 0 1010 292" role="img" aria-label="Selected error over actual Minecraft ticks" id="plot"></svg>
<div class="legend"><span><i class="dot" style="background:#5dd39e"></i>Source deviation from actual original Forge</span><span>Each line point is a synchronized real Entity tick</span></div>
<p id="description"></p></div>
<h2>Independently validated recordings</h2><div class="panel scroll"><table><thead><tr><th>Recorded scenario</th><th>Airframe</th><th>Ticks</th><th>One-step RMSE</th><th>Final open-loop drift</th><th>Evidence status</th></tr></thead><tbody id="records"></tbody></table></div>
<footer>Source model: pinned IA 1.3.3 five-harmonic aerodynamic perturbation + exact original per-airframe engine response. Runtime provenance requires the separate original Forge GameTest / pinned-JAR verification. No overall Minecraft parity certificate; no B-17 mission protection threshold changes.</footer></main>
<script>const evidence="""+embedded+""";
const sel=document.getElementById('scene'),metric=document.getElementById('metric'),chart=document.getElementById('plot');
const fixed=(v,n=6)=>Number(v).toFixed(n);
document.getElementById('cases').textContent=evidence.traces.length;
document.getElementById('types').textContent=new Set(evidence.traces.map(x=>x.aircraft)).size;
document.getElementById('ticks').textContent=evidence.traces.reduce((a,b)=>a+b.ticks,0).toLocaleString();
document.getElementById('max').textContent=fixed(Math.max(...evidence.traces.map(x=>x.free_run_final_position_error_blocks)));
for(const item of evidence.traces){const opt=document.createElement('option');opt.value=item.scenario;opt.textContent=item.scenario+' · '+item.aircraft;sel.append(opt);
const tr=document.createElement('tr');for(const val of [item.scenario,item.aircraft,item.ticks,fixed(item.one_step_position_rmse_blocks,9),fixed(item.free_run_final_position_error_blocks,6),item.roll_status==='OBSERVED'?'Real roll observed':'Roll not in trace']){const td=document.createElement('td');td.textContent=String(val);tr.append(td)}document.getElementById('records').append(tr)}
function draw(){const a=evidence.series[sel.value]||[],v=metric.value;if(!a.length)return;const nums=a.map(d=>d[v]);
const high=Math.max(0,...nums),low=Math.min(0,...nums),span=Math.max(1e-9,high-low);const x=i=>48+i*935/Math.max(1,a.length-1);
const y=z=>255-(z-low)/span*216;const make=(tag,attrs)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,val] of Object.entries(attrs))n.setAttribute(k,val);return n};
chart.replaceChildren();for(let i=0;i<=4;i++){let yi=29+i*54;chart.append(make('line',{x1:48,y1:yi,x2:985,y2:yi,stroke:'#244056','stroke-width':'1'}));
const label=make('text',{x:3,y:yi+4});label.textContent=(high-(span*i/4)).toFixed(Math.abs(high)<.01?5:2);chart.append(label)}
const poly=make('polyline',{points:nums.map((z,i)=>x(i)+','+y(z)).join(' '),stroke:'#5dd39e','stroke-width':'2.2',fill:'none', 'stroke-linejoin':'round'});chart.append(poly);
const n=make('text',{x:933,y:283});n.textContent=a.length+' ticks';chart.append(n);
const item=evidence.traces.find(z=>z.scenario===sel.value);document.getElementById('description').textContent=
'Recorded airframe '+item.aircraft+' · '+item.ticks+' original-Forge physics steps · one-step position RMSE '+fixed(item.one_step_position_rmse_blocks,9)+' blocks · final predicted position difference '+fixed(item.free_run_final_position_error_blocks,6)+' blocks. '+(item.kind==='tactical_pinned_wind'?'Controller decisions are prerecorded, not freshly simulated.':'Neutral controls are re-integrated from actual takeoff state.');}
sel.addEventListener('change',draw);metric.addEventListener('change',draw);draw();</script></body></html>"""


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--twin-dir",type=Path,required=True)
    parser.add_argument("--original-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--expect-roster",type=int,default=0)
    parser.add_argument("--expect-neutral",type=int,default=0)
    parser.add_argument("--expect-tactical",type=int,default=0)
    parser.add_argument("--max-final-drift",type=float)
    args=parser.parse_args()
    try:
        result=verify(args.twin_dir,args.original_dir,args.output_dir,args.expect_roster,
                      args.expect_neutral,args.expect_tactical,args.max_final_drift)
    except (OSError,ValueError) as exc:
        raise SystemExit("TWIN_RECEIPT_PROVENANCE_FAILED: "+str(exc)) from None
    print(json.dumps({key:value for key,value in result.items() if key!="trace_metrics"},indent=2,sort_keys=True))
    if result["failed_gates"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

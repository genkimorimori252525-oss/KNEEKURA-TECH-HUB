#!/usr/bin/env python3
"""Render deterministic Flight Research Batch outputs as a standalone file:// HTML.

Python standard library only. Every trace and aggregate is embedded as JSON
inside the output page; no fetch(), CDN, webfont, browser server, or JS library.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SCHEMA = "ww.flight-research-lab.v1"
NUMERIC = {
    "tick", "seconds", "x", "y", "z", "vx", "vy", "vz",
    "speed_bps", "yaw_deg", "pitch_deg", "roll_deg",
    "raw_x", "raw_z", "engine_target", "engine_power",
    "ground_y", "clearance", "wind_stress_multiplier",
}


def load_experiment(summary_path: Path, slices_path: Path) -> dict:
    with summary_path.open(encoding="utf-8") as stream:
        summary = json.load(stream)
    if summary.get("schema") != SCHEMA or "NO_FORGE_PARITY" not in summary.get("evidence", ""):
        raise ValueError("Refusing non-lab or misleading provenance")
    required = {"trial_id", "aircraft_id", "role", "scenario", "tick", "x", "y", "z"}
    traces: dict[str, list[dict]] = {}
    total_rows = 0
    with slices_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(f"Missing trajectory fields: {sorted(required - set(reader.fieldnames or []))}")
        for line in reader:
            if line["schema"] != SCHEMA:
                raise ValueError("Time-slice schema mismatch")
            point = {key: float(value) if key in NUMERIC else value for key, value in line.items()}
            point["on_ground"] = line["on_ground"] == "true"
            trial_id = line["trial_id"]
            traces.setdefault(trial_id, []).append(point)
            total_rows += 1
    if total_rows != summary["sampled_time_slice_rows"]:
        raise ValueError(
            f"Trace row mismatch: generated {total_rows}; summary says "
            f"{summary['sampled_time_slice_rows']}"
        )
    if len(traces) != summary["sampled_traces"]:
        raise ValueError("Trace count mismatch")
    by_pair: dict[str, list[dict]] = {}
    for trial_id, points in traces.items():
        if not points or points[0]["tick"] != 0 or points[-1]["tick"] != summary["ticks_per_trial"]:
            raise ValueError(f"Missing trajectory endpoint: {trial_id}")
        if [p["tick"] for p in points] != sorted({p["tick"] for p in points}):
            raise ValueError(f"Unordered/repeated time slice: {trial_id}")
        pair = points[0]["aircraft_id"] + "|" + points[0]["scenario"]
        by_pair.setdefault(pair, []).extend(points)
    return {"summary": summary, "traces": by_pair}


HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Warfare Wings | Flight Research Lab</title>
<style>
:root{color-scheme:dark;--bg:#08111e;--panel:#0e1b2b;--border:#2a3d52;--ink:#e8f3ff;--muted:#a6bccf;--cyan:#51dfe6;--amber:#ffa65d;--green:#96e2b1}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1500px;margin:auto;padding:24px clamp(12px,3vw,36px) 56px}
header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;flex-wrap:wrap}
h1{font-size:clamp(1.7rem,3vw,2.6rem);font-weight:730;letter-spacing:-.035em;margin:2px 0}
h2{font-size:1.08rem;margin:0 0 10px;color:#cee6fa}
p{margin:7px 0;color:var(--muted)}
.eyebrow{text-transform:uppercase;color:var(--cyan);font-size:.72rem;font-weight:800;letter-spacing:.18em}
.provenance{max-width:550px;color:#f5c8a3;font-size:.88rem;border-left:3px solid var(--amber);padding:9px 14px;background:#1e2230}
.stats{display:grid;grid-template-columns:repeat(5,minmax(120px,1fr));gap:10px;margin:24px 0}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:13px 16px}
.stat strong{display:block;font-size:clamp(1.25rem,1.6vw,1.75rem);line-height:1.4;letter-spacing:-.03em}
.stat small{color:var(--muted)}
.toolbar{display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;background:var(--panel);border:1px solid var(--border);padding:16px;border-radius:13px}
label{color:var(--muted);font-size:.83rem;font-weight:650}
label select{display:block;margin-top:5px}
select{color:var(--ink);border:1px solid #41576f;border-radius:8px;background:#14283c;padding:9px 12px;min-width:225px;font:inherit}
.span{flex:1}
.readout{font-family:ui-monospace,Consolas,monospace;font-size:.85rem;color:var(--cyan)}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:13px;padding:16px;min-width:0}
.charts{display:grid;grid-template-columns:1.35fr 1fr;gap:12px;margin:12px 0}
.projection-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.chart-title{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.chart-title small{color:var(--muted)}
canvas{display:block;width:100%;height:auto;background:#081521;border:1px solid #213347;border-radius:8px}
input[type=range]{width:145px;accent-color:var(--cyan)}
.table-wrap{overflow:auto;max-height:480px}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.88rem}
th{text-align:right;padding:10px 12px;color:var(--muted);position:sticky;top:0;background:#102137;border-bottom:1px solid #41576f;white-space:nowrap}
td{text-align:right;padding:10px 12px;border-bottom:1px solid #263b50}
th:first-child,td:first-child{text-align:left}
tbody tr{cursor:pointer}tbody tr:hover{background:#1a3548}tbody tr.active{background:#174b5a}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:.8rem;color:var(--muted);margin-top:8px}
.legend span:before{content:"";display:inline-block;width:17px;height:3px;vertical-align:middle;margin-right:7px;background:var(--cyan)}
.legend .ground:before{background:var(--amber)}
.legend .alt:before{background:var(--green)}
.note{padding:12px 0;color:var(--muted)}
details{margin-top:18px;color:var(--muted);border-top:1px solid var(--border);padding-top:14px}
details summary{cursor:pointer;color:var(--ink)}
code{overflow-wrap:anywhere;color:#b3eaff}
@media(max-width:1000px){.stats{grid-template-columns:repeat(3,1fr)}.charts{grid-template-columns:1fr}}
@media(max-width:650px){.stats{grid-template-columns:repeat(2,1fr)}.projection-grid{grid-template-columns:1fr}}
</style>
</head>
<body><main>
<header>
  <div><div class="eyebrow">KNEEKURA / WARFARE WINGS / RESEARCH</div>
    <h1>Flight Research Lab</h1>
    <p>20 Hz・24機種の物理SOURCE実験。機種と課題を選んで飛跡と制御応答を比較する。</p>
  </div>
  <div class="provenance">SOURCE MICROKERNEL / 未校正の研究出力。Minecraft/Forgeの移動・衝突・風・武装と同等の動作を保証する測定ではありません。</div>
</header>
<section class="stats" id="global-stats" aria-label="バッチ実験規模"></section>
<section class="toolbar" aria-label="実験切り替え">
  <label>機種 <select id="aircraft"></select></label>
  <label>実験条件 <select id="scenario"></select></label>
  <label>立体投影角 <input type="range" min="-180" max="180" step="5" value="30" id="rotation"></label>
  <div class="span"></div><div id="flight-readout" class="readout"></div>
</section>
<div class="charts">
  <section class="panel">
    <div class="chart-title"><h2>3D風飛行軌跡</h2><small>Y＝高度 / X・Z＝水平方向（透視補正なし）</small></div>
    <canvas id="plot3d" width="840" height="430" role="img" aria-label="俯瞰回転可能な立体投影飛行軌跡"></canvas>
    <div class="legend"><span>飛行軌跡</span><span class="ground">接地時</span></div>
  </section>
  <div class="projection-grid">
    <section class="panel"><div class="chart-title"><h2>上面図 X / Z</h2><small>航跡 / blocks</small></div>
      <canvas id="plotTop" width="520" height="420" role="img" aria-label="X対Z平面航跡"></canvas></section>
    <section class="panel"><div class="chart-title"><h2>側面図 Z / Y</h2><small>高度 / blocks</small></div>
      <canvas id="plotSide" width="520" height="420" role="img" aria-label="Z対Y平面航跡"></canvas></section>
  </div>
</div>
<section class="panel">
  <div class="chart-title"><h2>時系列：速度・地表との距離</h2><small>横軸＝tick（20 tick / 秒）</small></div>
  <canvas id="plotTime" width="1360" height="260" role="img" aria-label="速度と地形クリアランス推移"></canvas>
  <div class="legend"><span>速度 / blocks per second</span><span class="alt">地形クリアランス / blocks</span></div>
</section>
<section class="panel" style="margin-top:12px">
  <div class="chart-title"><h2>全24機比較：選択した実験条件</h2><small>平均値は各試行を同じ重みで集計</small></div>
  <div class="table-wrap"><table>
    <thead><tr><th>機種</th><th>試行</th><th>平均速度 b/s</th><th>平均航続距離 blocks</th>
      <th>平均最小高度 blocks</th><th>接地した試行</th><th>90°到達試行</th><th>安全制御介入 tick</th></tr></thead>
    <tbody id="comparison"></tbody>
  </table></div>
</section>
<details><summary>モデルの出典・実験上の制約</summary>
 <p>物理計算は <code>Ia133Microkernel.tickWithReaction</code> を毎tick実行。24機種の有効モデルは同一ANCHOR由来のAtlas CSV、エンジン反応時間はクラスごとに抽出された値を使用。</p>
 <p>風はSOURCEの入力へ渡した人為的な周期変動。地形は解析式の尾根形状と座標ごとの高度サンプリングであり、Minecraftの当たり判定ではない。敵機は目撃された直線運動の観測値としてのみ登場し、戦闘結果や射撃命中率を再現しない。</p>
 <p>この表示は代表試行（機種×課題ごとに1件）の時系列。表の平均は全試行を使用。パラメータと個別試行は <code>summary.json</code>・<code>outcomes.csv</code>・<code>time_slices.csv</code> に保存されている。</p>
 <p id="identity"></p>
</details>
</main>
<script>
"use strict";
const DATA = __LAB_DATA__;
const summary = DATA.summary;
const groups = summary.groups;
const traces = DATA.traces;
const $ = id => document.getElementById(id);
const fmt = (v, digits=1) => Number.isFinite(Number(v)) ? Number(v).toFixed(digits) : "—";
const sortedIds = [...new Set(groups.map(g => g.aircraft_id))].sort();
const scenarioNames = summary.scenarios;
const labelId = id => id.replace("warfare_wings:", "").toUpperCase();
$("aircraft").innerHTML = sortedIds.map(id => '<option value="' + id + '">' + labelId(id) + '</option>').join("");
$("scenario").innerHTML = scenarioNames.map(sc => '<option value="' + sc + '">' + sc.replace(/_/g," ") + '</option>').join("");
$("aircraft").value = sortedIds.includes("warfare_wings:a6m") ? "warfare_wings:a6m" : sortedIds[0];
$("scenario").value = "TURN_LEFT";
const stats = [
  [summary.aircraft_count, "収録機種"],
  [summary.scenario_count, "実験条件"],
  [summary.trial_count.toLocaleString("ja-JP"), "独立試行"],
  [summary.simulated_ticks.toLocaleString("ja-JP"), "SOURCE物理tick"],
  [summary.seed, "基準seed"]
];
$("global-stats").innerHTML = stats.map(([val,label]) => '<div class="stat"><strong>'+val+'</strong><small>'+label+'</small></div>').join("");
$("identity").textContent = "Anchor SHA-256: "+summary.aircraft_anchor_sha256+
  " | IA commit: "+summary.immersive_aircraft_source_commit+
  " | evidence: "+summary.evidence;

function domain(points, xField, yField) {
  const xs = points.map(p => xField(p)), ys = points.map(p => yField(p));
  const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
  const dx = Math.max(1, maxx-minx), dy = Math.max(1, maxy-miny);
  return {minx, maxx, miny, maxy, dx, dy};
}
function prep(canvas) {
  const ctx=canvas.getContext("2d");
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle="#081521";ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle="#203247";ctx.lineWidth=1;
  const pad=34,w=canvas.width,h=canvas.height;
  for(let n=0;n<=5;n++){
    let x=pad+(w-2*pad)*n/5,y=pad+(h-2*pad)*n/5;
    ctx.beginPath();ctx.moveTo(x,pad);ctx.lineTo(x,h-pad);ctx.stroke();
    ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke();
  }
  return {ctx,pad,w,h};
}
function tracePlot(id,points,project) {
  const canvas=$(id),{ctx,pad,w,h}=prep(canvas);
  if (!points.length) return;
  const projected=points.map(project);
  const ds=domain(projected,p=>p[0],p=>p[1]);
  const scale=Math.min((w-pad*2)/ds.dx,(h-pad*2)/ds.dy)*0.88;
  const midx=(ds.minx+ds.maxx)/2,midy=(ds.miny+ds.maxy)/2;
  const plot=p=>[w/2+(p[0]-midx)*scale,h/2-(p[1]-midy)*scale];
  ctx.lineCap="round";ctx.lineJoin="round";
  for(let i=1;i<points.length;i++){
    const a=plot(projected[i-1]),b=plot(projected[i]);
    ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);
    ctx.lineWidth=3;ctx.strokeStyle=points[i].on_ground?"#ffa65d":"#51dfe6";ctx.stroke();
  }
  const first=plot(projected[0]),last=plot(projected[projected.length-1]);
  for(const [pt,color] of [[first,"#96e2b1"],[last,"#ffffff"]]){
    ctx.beginPath();ctx.arc(pt[0],pt[1],6,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();
  }
  ctx.font="16px ui-monospace,monospace";ctx.fillStyle="#a9bdce";
  ctx.fillText("scale "+fmt(Math.max(ds.dx,ds.dy),1)+" blocks (largest span)",pad,21);
}
function timePlot(points) {
  const canvas=$("plotTime"),{ctx,pad,w,h}=prep(canvas);
  if(!points.length)return;
  const maxT=summary.ticks_per_trial;
  const maxSpeed=Math.max(1,...points.map(p=>p.speed_bps));
  const maxHeight=Math.max(1,...points.map(p=>p.clearance));
  const y0=h-pad;
  const draw=(field,max,color)=>{
    ctx.beginPath();
    points.forEach((p,i)=>{
      const x=pad+(w-2*pad)*p.tick/maxT;
      const y=y0-(h-pad*2)*Math.max(0,Math.min(1,p[field]/max));
      i?ctx.lineTo(x,y):ctx.moveTo(x,y);
    });
    ctx.strokeStyle=color;ctx.lineWidth=3;ctx.stroke();
  };
  draw("speed_bps",maxSpeed,"#51dfe6");
  draw("clearance",maxHeight,"#96e2b1");
  ctx.font="16px ui-monospace,monospace";ctx.fillStyle="#a9bdce";
  ctx.fillText("speed max "+fmt(maxSpeed,1)+" b/s   clearance max "+fmt(maxHeight,1)+" blocks",pad,21);
  ctx.fillText("tick 0",pad,h-9);
  ctx.fillText("tick "+maxT,w-pad-110,h-9);
}
function updateTable(sc,id) {
  const items=groups.filter(g=>g.scenario===sc).sort((a,b)=>a.aircraft_id.localeCompare(b.aircraft_id));
  $("comparison").innerHTML=items.map(g=>
    '<tr data-id="'+g.aircraft_id+'" class="'+(g.aircraft_id===id?'active':'')+'">' +
    '<td>'+labelId(g.aircraft_id)+'</td><td>'+g.trial_count+'</td>' +
    '<td>'+fmt(g.mean_speed_bps,2)+'</td><td>'+fmt(g.mean_path_blocks,1)+'</td>' +
    '<td>'+fmt(g.mean_min_clearance_blocks,1)+'</td>' +
    '<td>'+g.ground_contact_trials+'</td><td>'+g.reached_90_yaw_trials+'</td>' +
    '<td>'+g.safety_override_ticks+'</td></tr>'
  ).join("");
  document.querySelectorAll("#comparison tr").forEach(tr=>tr.addEventListener("click",()=>{
    $("aircraft").value=tr.dataset.id;update();
  }));
}
function update() {
  const id=$("aircraft").value,sc=$("scenario").value;
  const g=groups.find(x=>x.aircraft_id===id&&x.scenario===sc);
  const pts=traces[id+"|"+sc]||[];
  const theta=Number($("rotation").value)*Math.PI/180;
  const origin=pts[0]||{x:0,y:0,z:0};
  const relative=p=>({x:p.x-origin.x,y:p.y-origin.y,z:p.z-origin.z});
  tracePlot("plot3d",pts,p=>{
    const q=relative(p),u=q.x*Math.cos(theta)-q.z*Math.sin(theta);
    const depth=q.x*Math.sin(theta)+q.z*Math.cos(theta);
    return [u, q.y*1.3-depth*.55];
  });
  tracePlot("plotTop",pts,p=>[p.x,p.z]);
  tracePlot("plotSide",pts,p=>[p.z,p.y]);
  timePlot(pts);
  $("flight-readout").textContent=g ?
     "n="+g.trial_count+" | v̄="+fmt(g.mean_speed_bps,2)+" b/s | clearance(min)="+
     fmt(g.mean_min_clearance_blocks,1)+" blocks | reaction="+g.engine_reaction_ticks+" tick" :
     "No result";
  updateTable(sc,id);
}
$("aircraft").addEventListener("change",update);
$("scenario").addEventListener("change",update);
$("rotation").addEventListener("input",update);
update();
</script></body></html>
"""


def make_html(summary: Path, slices: Path, output: Path) -> dict:
    payload = load_experiment(summary, slices)
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    # A source dataset may contain arbitrary aircraft labels; protect inline JS.
    embedded = embedded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(HTML.replace("__LAB_DATA__", embedded), encoding="utf-8", newline="\n")
    return payload["summary"]


TWIN_NUMBERS = {
    "engine_reaction_ticks",
    "tick", "seconds", "x", "y", "z", "vx", "vy", "vz", "speed_bps",
    "yaw_deg", "pitch_deg", "roll_deg", "engine_target", "engine_power",
    "ground_y", "clearance_blocks", "nearest_ally_blocks", "team_known_count",
    "visible_hostiles_count", "stale_tracks_count", "los_rejected_count",
    "fov_rejected_count", "out_of_range_count", "contact_age_ticks",
    "control_x", "control_z", "control_throttle", "range_blocks",
    "nose_dot", "ray_clearance_blocks", "track_age_ticks",
    "initial_separation_blocks", "min_sampled_separation_blocks",
    "min_swept_center_separation_blocks", "sampled_lt6_ticks", "swept_lt6_ticks",
    "closest_sampled_tick", "closest_swept_tick", "final_separation_blocks",
    "protection_radius_blocks", "initial_closest_hostile_blocks",
    "min_sampled_hostile_blocks", "min_swept_hostile_blocks",
    "within95_sampled_ticks", "within95_swept_ticks", "first_intrusion_sampled_tick",
    "first_intrusion_swept_tick", "escort_target_assignment_ticks",
    "first_escort_assignment_tick", "interposition_ticks", "bomber_path_blocks",
    "bomber_ground_ticks", "bomber_final_speed_bps", "bomber_final_objective_distance",
    "path_blocks", "displacement_blocks", "initial_speed_bps", "final_speed_bps",
    "final_objective_distance", "min_clearance_blocks", "ground_ticks",
    "visible_contact_ticks", "first_visible_tick", "stale_track_ticks",
    "first_stale_tick", "track_expiration_events", "los_blocked_observations",
    "fov_blocked_observations", "range_blocked_observations",
    "assigned_target_ticks", "first_assignment_tick", "collision_avoidance_ticks",
    "terrain_safety_ticks", "safety_override_ticks", "decision_changes",
    "advisory_fire_ticks",
}
TWIN_BOOL = {"on_ground", "track_available", "current_observation", "track_expired"}
TWIN_SCHEMA = "ww.flight-twin.closed-loop.v1"


def load_twin_experiment(output_dir: Path) -> dict:
    with (output_dir / "twin_summary.json").open(encoding="utf-8") as stream:
        summary = json.load(stream)
    if (summary.get("schema") != TWIN_SCHEMA
            or "NO_FORGE_PARITY" not in summary.get("evidence", "")
            or summary.get("body_separation_radius_blocks") != 6.0
            or summary.get("b17_protection_radius_blocks") != 95.0):
        raise ValueError("Twin provenance or original undiluted safety radii are invalid")
    wanted = {
        "units": "twin_units.csv", "pairs": "twin_pairs.csv",
        "assets": "twin_assets.csv", "slices": "twin_time_slices.csv",
        "events": "twin_sensor_events.csv",
    }
    payload = {"summary": summary}
    case_ids = {case["id"] for case in summary["scenarios"]}
    for key, filename in wanted.items():
        rows = []
        with (output_dir / filename).open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if "schema" not in (reader.fieldnames or []) or "scenario" not in (reader.fieldnames or []):
                raise ValueError(f"Malformed {filename}")
            for source in reader:
                if source["schema"] != TWIN_SCHEMA or source["scenario"] not in case_ids:
                    raise ValueError(f"Twin CSV record outside declared scope: {filename}")
                result = {}
                for field, value in source.items():
                    if field in TWIN_BOOL:
                        result[field] = value == "true"
                    elif field in TWIN_NUMBERS:
                        result[field] = float(value) if value else None
                    else:
                        result[field] = value
                rows.append(result)
        payload[key] = rows
    for case in summary["scenarios"]:
        name = case["id"]
        n = case["active_aircraft"]
        slices = [s for s in payload["slices"] if s["scenario"] == name]
        units = [s for s in payload["units"] if s["scenario"] == name]
        pairs = [s for s in payload["pairs"] if s["scenario"] == name]
        if len(units) != n or len(pairs) != n * (n - 1) // 2:
            raise ValueError(f"Missing complete per-aircraft/per-pair Twin outcome: {name}")
        if len({u["aircraft_id"] for u in units}) != case["unique_aircraft_types"]:
            raise ValueError(f"Duplicate/missing aircraft types in {name}")
        if len({s["unit_id"] for s in slices if s["tick"] == 0}) != n:
            raise ValueError(f"Missing t0 Twin snapshot for {name}")
        if len({s["unit_id"] for s in slices if s["tick"] == case["simulated_ticks"]}) != n:
            raise ValueError(f"Missing final Twin snapshot for {name}")
        if sum(int(p["swept_lt6_ticks"]) for p in pairs) != case["swept_lt6_pair_ticks"]:
            raise ValueError(f"Silent body-separation gate mismatch in {name}")
        asset_rows = [s for s in payload["assets"] if s["scenario"] == name]
        if sum(int(a["within95_swept_ticks"]) for a in asset_rows) != case["swept_within95_hostile_ticks"]:
            raise ValueError(f"Silent B17 radius gate mismatch in {name}")
        gates_fail = (any(p["body_gate"] == "FAILED" for p in pairs)
                      or any(a["protection_gate"] == "FAILED" for a in asset_rows)
                      or any(u["ground_ticks"] > 0 for u in units))
        if gates_fail != (case["status"] == "FAILED_SOURCE_SAFETY"):
            raise ValueError(f"Reported safety result does not reflect evidence: {name}")
    return payload


TWIN_HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Warfare Wings · Closed-Loop Flight Twin</title>
<style>
:root{color-scheme:dark;--bg:#09121d;--panel:#101f30;--grid:#294052;--text:#e5f0ff;--mute:#a4b7ce;--a:#6de2e4;--b:#ffb772;--warn:#fa7373}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,"Segoe UI",sans-serif}
main{max-width:1510px;margin:auto;padding:24px clamp(12px,3vw,34px) 70px}
header{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;flex-wrap:wrap}h1{font-size:clamp(1.65rem,3.2vw,2.65rem);margin:0;letter-spacing:-.045em}
h2{font-size:1.07rem;margin:0 0 9px}p{color:var(--mute);margin:6px 0}
.tag{font-size:.72rem;letter-spacing:.14em;font-weight:750;color:var(--a)}
.note{max-width:525px;border-left:3px solid var(--b);padding:7px 14px;background:#202739;color:#f0d1b4;font-size:.88rem}
.controls{display:flex;align-items:end;gap:14px;flex-wrap:wrap;margin:22px 0 12px;background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:15px}
label{font-size:.83rem;color:var(--mute)}select,input{display:block;margin-top:5px;padding:8px;background:#142c42;border:1px solid #486076;border-radius:8px;color:var(--text);font:inherit}
input[type=range]{width:230px;padding:0;accent-color:var(--a)}select{min-width:240px}
.fill{flex:1}.metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-bottom:12px}
.metric,.panel{background:var(--panel);border:1px solid var(--grid);border-radius:12px;padding:14px}
.metric strong{display:block;font-size:clamp(1.03rem,1.55vw,1.6rem);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.metric small{color:var(--mute)}.plots{display:grid;grid-template-columns:1.2fr 1fr;gap:12px}
.stack{display:grid;gap:12px}canvas{width:100%;height:auto;display:block;border-radius:7px;background:#081624;border:1px solid #22374c}
.label{display:flex;gap:10px;align-items:center;justify-content:space-between;color:var(--mute);font-size:.78rem;margin-bottom:8px}
.legend{display:flex;gap:18px;color:var(--mute);font-size:.8rem;margin:10px 0 0}
.legend span::before{content:"";display:inline-block;width:16px;height:3px;background:var(--a);vertical-align:middle;margin-right:6px}
.legend .enemy::before{background:var(--b)}.legend .danger::before{background:var(--warn)}
.tables{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.scroll{max-height:350px;overflow:auto}table{width:100%;border-collapse:collapse;font-size:.82rem;font-variant-numeric:tabular-nums}
th,td{padding:9px 10px;border-bottom:1px solid #2a4054;text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{position:sticky;top:0;background:#152a3d;color:var(--mute)}
td.bad{color:var(--warn);font-weight:750}.status{font-family:ui-monospace,Consolas,monospace;font-size:.82rem;overflow-wrap:anywhere}
details{margin-top:19px;color:var(--mute)}details summary{cursor:pointer;color:var(--text)}
code{color:#b7ecf1;overflow-wrap:anywhere}
@media(max-width:1020px){.metrics{grid-template-columns:repeat(3,1fr)}.plots,.tables{grid-template-columns:1fr}}
@media(max-width:550px){.metrics{grid-template-columns:repeat(2,1fr)}}
</style></head>
<body><main>
<header><div><span class="tag">KNEEKURA · WARFARE WINGS · 20 HZ</span>
  <h1>Closed-Loop Flight Twin</h1>
  <p>敵機を観測 → 視野・地形LOS → 記憶 → 指令 → 機体ごとのSOURCE物理。全機が同じtickで進行。</p></div>
  <div class="note">SOURCE実験結果。地形LOS・機体間隔・敵発見は人工的な研究モデルです。Forgeの衝突・チャンク・視線・射撃の実機合格を意味しません。</div></header>
<div class="controls">
  <label>同時飛行シナリオ<select id="scene"></select></label>
  <label>時刻 / tick<input id="time" type="range" min="0" max="240" step="1" value="0"></label>
  <label>軌跡の選択<select id="selected"></select></label><div class="fill"></div>
  <span class="status" id="timestamp"></span>
</div>
<section class="metrics" id="metrics"></section>
<div class="plots">
  <section class="panel"><div class="label"><h2>上面図 X / Z · 現在位置と実際の飛跡</h2><span>単位: blocks · 線は観測目標/記憶</span></div>
    <canvas id="top" width="810" height="590" role="img" aria-label="24機までの同時航空機位置と実際の航跡"></canvas>
    <div class="legend"><span>青チーム</span><span class="enemy">赤チーム</span><span class="danger">6b侵入、95b保護境界</span></div>
  </section>
  <div class="stack">
   <section class="panel"><div class="label"><h2>立体風投影 / 3D trajectory</h2><span>高度と各隊形</span></div>
     <canvas id="iso" width="720" height="350" role="img" aria-label="機体軌跡の高度つき俯瞰投影"></canvas></section>
   <section class="panel"><div class="label"><h2>断面図 Z / Y</h2><span>地形、上下運動</span></div>
     <canvas id="side" width="720" height="300" role="img" aria-label="Zと高度の時間経過"></canvas></section>
  </div>
</div>
<div class="tables">
 <section class="panel"><h2>全機体の判断・視認・間隔</h2><div class="scroll"><table><thead><tr>
  <th>機体</th><th>速度 b/s</th><th>現在の判断</th><th>視認数</th><th>記憶数</th><th>LOS遮蔽</th></tr></thead><tbody id="unitTable"></tbody></table></div></section>
 <section class="panel"><h2>原型の安全条件・測定結果</h2><div class="scroll"><table><thead><tr>
  <th>対象</th><th>最小距離</th><th>しきい値</th><th>侵犯tick</th><th>判定</th></tr></thead><tbody id="gateTable"></tbody></table></div>
  <p id="gates" class="status"></p></section>
</div>
<details><summary>データ出典と限界</summary>
 <p>飛行物理: <code>Ia133Microkernel.tickWithReaction</code> + <code>PinnedIa133WindWorld.calmAirCalibration().windAfterFriction</code>、24の原本由来モデルとエンジン応答値。20Hzの全機同期更新。チーム位置は理想化された味方無線と見なす。敵情報は各機の独立した距離/3D FOV/高さ地形LOS/時間制限付き記憶だけで取得。</p>
 <p>相互距離は機体中心間の距離。各tick端点と、両者が1 tick中に直線移動したとみなす保守的な最近接距離を別々に測定する。6bは機体衝突そのもの、95bは飛行中のB17への敵機侵入をMinecraftの実衝突判定に置き換えるものではない。後方配置/前方配置の位置としきい値は既存の原型テストから一切変更していない。</p>
 <p>ログ: <code>twin_summary.json</code>, <code>twin_units.csv</code>, <code>twin_pairs.csv</code>, <code>twin_assets.csv</code>, <code>twin_time_slices.csv</code>, <code>twin_sensor_events.csv</code>。HTMLはこれらのデータを内蔵し、外部通信を使わない。</p>
 <p id="provenance"></p>
</details>
</main>
<script>
"use strict";
const DATA=__TWIN_DATA__,summary=DATA.summary;
const get=id=>document.getElementById(id),f=(x,n=1)=>Number.isFinite(Number(x))?Number(x).toFixed(n):"—";
const scenes=summary.scenarios;
get("scene").innerHTML=scenes.map(x=>'<option value="'+x.id+'">'+x.id.replace(/_/g," ")+'</option>').join("");
get("scene").value=scenes.some(x=>x.id==="original_b17_aft")?"original_b17_aft":scenes[0].id;
get("provenance").textContent=summary.evidence+" / anchor SHA-256 "+summary.aircraft_anchor_sha256;
function colour(team){return team==="blue"||team==="a"?"#6de2e4":"#ffb772"}
function points(scene){return DATA.slices.filter(p=>p.scenario===scene)}
function prepare(id){const c=get(id),ctx=c.getContext("2d");ctx.fillStyle="#081624";ctx.fillRect(0,0,c.width,c.height);
  ctx.strokeStyle="#20354b";ctx.lineWidth=1;
  for(let i=0;i<=6;i++){let x=32+(c.width-64)*i/6,y=32+(c.height-64)*i/6;
    ctx.beginPath();ctx.moveTo(x,26);ctx.lineTo(x,c.height-26);ctx.stroke();
    ctx.beginPath();ctx.moveTo(26,y);ctx.lineTo(c.width-26,y);ctx.stroke();}
  return {ctx,w:c.width,h:c.height,pad:38};}
function viewport(pts,id,project,extra=0){
  const chart=prepare(id),coords=pts.map(project);
  if(!coords.length)return null;
  const xs=coords.map(p=>p[0]),ys=coords.map(p=>p[1]),bounds=[
    Math.min(...xs)-extra,Math.max(...xs)+extra,Math.min(...ys)-extra,Math.max(...ys)+extra];
  const dx=Math.max(1,bounds[1]-bounds[0]),dy=Math.max(1,bounds[3]-bounds[2]);
  const scale=Math.min((chart.w-chart.pad*2)/dx,(chart.h-chart.pad*2)/dy)*.91;
  const mx=(bounds[0]+bounds[1])/2,my=(bounds[2]+bounds[3])/2;
  const xy=p=>[chart.w/2+(p[0]-mx)*scale,chart.h/2-(p[1]-my)*scale];
  return {...chart,scale,xy};}
function drawChart(canvasId,rows,now,project,b17){
  const own=rows.filter(p=>p.tick<=now);
  const extra=(canvasId==="top" && b17)?95:0;
  const view=viewport(own,canvasId,project,extra);
  if(!view)return;
  const {ctx,xy,scale}=view;
  const grouped={};
  for(const p of own)(grouped[p.unit_id]??=[]).push(p);
  if(canvasId==="top" && b17){
    const bomber=own.filter(p=>p.unit_id===b17).at(-1);
    if(bomber){const c=xy(project(bomber));ctx.strokeStyle="#fa7373";ctx.setLineDash([7,5]);
      ctx.lineWidth=2;ctx.beginPath();ctx.arc(c[0],c[1],95*scale,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle="#f3a4a4";ctx.font="13px Consolas,monospace";ctx.fillText("B-17: 95 blocks",c[0]+7,c[1]-95*scale+14);}
  }
  for(const [id,track] of Object.entries(grouped)){
    ctx.strokeStyle=colour(track[0].team);ctx.lineWidth=1.7;ctx.globalAlpha=.48;
    ctx.beginPath();track.forEach((p,i)=>{const c=xy(project(p));i?ctx.lineTo(...c):ctx.moveTo(...c)});ctx.stroke();ctx.globalAlpha=1;
    const last=track.at(-1),pos=xy(project(last)),focused=get("selected").value===id;
    ctx.fillStyle=colour(last.team);ctx.beginPath();ctx.arc(pos[0],pos[1],focused?7:4.3,0,Math.PI*2);ctx.fill();
    if(focused){ctx.strokeStyle="#fff";ctx.lineWidth=2;ctx.beginPath();ctx.arc(pos[0],pos[1],10,0,Math.PI*2);ctx.stroke();}
    if(Object.keys(grouped).length<10||focused){ctx.font="12px ui-monospace,monospace";ctx.fillStyle="#e8f4ff";ctx.fillText(id,pos[0]+9,pos[1]-6);}
    if(focused && canvasId==="top" && last.observed_contact_id){
      const t=grouped[last.observed_contact_id]?.at(-1);
      if(t){ctx.strokeStyle=last.contact_age_ticks>0?"#ffaa8a":"#b9fbe9";
        ctx.setLineDash(last.contact_age_ticks>0?[4,5]:[]);ctx.beginPath();ctx.moveTo(...pos);
        ctx.lineTo(...xy(project(t)));ctx.stroke();ctx.setLineDash([]);}
    }
  }
  if(canvasId==="top"){
    for(const pair of DATA.pairs.filter(p=>p.scenario===get("scene").value && p.min_swept_center_separation_blocks<6)){
      const a=grouped[pair.first_unit]?.at(-1),b=grouped[pair.second_unit]?.at(-1);
      if(a&&b&&Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z)<6){
        ctx.strokeStyle="#fa7373";ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(...xy(project(a)));
        ctx.lineTo(...xy(project(b)));ctx.stroke();}
    }
  }
}
function rowForTick(data,tick){
  const available=[...new Set(data.map(x=>x.tick))].sort((a,b)=>a-b);
  return available.reduce((best,current)=>Math.abs(current-tick)<Math.abs(best-tick)?current:best,available[0]??0);
}
function refresh(){
 const name=get("scene").value,scene=scenes.find(x=>x.id===name),source=points(name);
 get("time").max=scene.simulated_ticks;
 const requested=Number(get("time").value),tick=rowForTick(source,requested);
 const allAt=source.filter(x=>x.tick===tick);
 if(!allAt.length)return;
 const prior=source.filter(x=>x.tick<=tick);
 const chosen=get("selected").value;
 if(!allAt.some(x=>x.unit_id===chosen)){
   const list=[...new Set(source.map(x=>x.unit_id))];
   get("selected").innerHTML=list.map(x=>'<option value="'+x+'">'+x+'</option>').join("");
   get("selected").value=list.find(x=>x==="cargo")||list[0];
 }
 const min=scene.min_swept_pair_separation_blocks;
 const result=[
  [scene.active_aircraft,"同時飛行中の機体"],
  [scene.simulated_ticks,"SOURCE 20Hz tick"],
  [scene.unique_aircraft_types,"異なる機種"],
  [f(min,2)+" b","全対の最小中心間隔"],
  [scene.swept_within95_hostile_ticks,"B17境界侵犯tick"],
  [scene.status==="PASS_SOURCE_SAFETY"?"SOURCE PASS":"SOURCE FAILED","原型の安全判定"]
 ];
 get("metrics").innerHTML=result.map(x=>'<div class="metric"><strong>'+x[0]+'</strong><small>'+x[1]+'</small></div>').join("");
 get("timestamp").textContent="sample tick "+tick+" / "+scene.simulated_ticks+"  ("+f(tick/20,1)+" s)";
 const asset=DATA.assets.find(x=>x.scenario===name);
 const b17=asset?.asset_unit;
 drawChart("top",prior,tick,p=>[p.x,p.z],b17);
 drawChart("iso",prior,tick,p=>[p.x*.76-p.z*.55,p.y*1.25-p.z*.38],null);
 drawChart("side",prior,tick,p=>[p.z,p.y],null);
 get("unitTable").innerHTML=allAt.map(u=>'<tr><td>'+u.unit_id+'</td><td>'+f(u.speed_bps,2)+
   '</td><td>'+u.maneuver+'</td><td>'+u.visible_hostiles_count+'</td><td>'+u.stale_tracks_count+
   '</td><td>'+u.los_rejected_count+'</td></tr>').join("");
 const pairRows=DATA.pairs.filter(x=>x.scenario===name).sort((a,b)=>a.min_swept_center_separation_blocks-b.min_swept_center_separation_blocks);
 const gateRows=pairRows.slice(0,Math.min(18,pairRows.length)).map(p=>[
    p.first_unit+" ↔ "+p.second_unit,f(p.min_swept_center_separation_blocks,2),"6 b",p.swept_lt6_ticks,p.body_gate]);
 for(const a of DATA.assets.filter(x=>x.scenario===name))
   gateRows.unshift([a.asset_unit+" / hostile",f(a.min_swept_hostile_blocks,2),"95 b",a.within95_swept_ticks,a.protection_gate]);
 get("gateTable").innerHTML=gateRows.map(r=>'<tr>'+r.map((v,i)=>'<td class="'+((i===4&&v==="FAILED")?"bad":"")+'">'+v+'</td>').join("")+'</tr>').join("");
 get("gates").textContent=scene.failed_operational_gates.length?
   "Source violations: "+scene.failed_operational_gates.join(" | "):
   "6b/95b/ground source criteria: no breach detected in sampled scenario.";
}
get("scene").addEventListener("change",()=>{get("time").value=0;get("selected").value="";refresh()});
get("time").addEventListener("input",refresh);
get("selected").addEventListener("change",refresh);
refresh();
</script></body></html>
"""


def make_twin_html(output_dir: Path, html: Path) -> dict:
    payload = load_twin_experiment(output_dir)
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    embedded = (embedded.replace("<", "\\u003c")
                .replace(">", "\\u003e").replace("&", "\\u0026"))
    html.parent.mkdir(parents=True, exist_ok=True)
    html.write_text(TWIN_HTML.replace("__TWIN_DATA__", embedded), encoding="utf-8", newline="\n")
    return payload["summary"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="Java batch summary.json")
    parser.add_argument("slices", type=Path, help="Java batch time_slices.csv")
    parser.add_argument("html", type=Path, help="Target standalone local HTML")
    args = parser.parse_args()
    summary = make_html(args.summary, args.slices, args.html)
    print(f"FLIGHT_LAB_REPORT PASS {args.html} "
          f"aircraft={summary['aircraft_count']} traces={summary['sampled_traces']}")


if __name__ == "__main__":
    main()

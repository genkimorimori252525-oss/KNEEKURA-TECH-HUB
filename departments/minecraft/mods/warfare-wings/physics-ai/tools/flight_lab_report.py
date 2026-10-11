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

#!/usr/bin/env python3
"""Build AI-readable and human-readable views from Warfare Wings source Atlas v2.

No composite strongest-aircraft score is produced. Fixed-duration and equal-angle turn metrics are
kept separate because they answer different questions.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from pathlib import Path

SCHEMA="ww.physics.aircraft-atlas-ai.v2"
SOURCE_SCHEMA="ww.physics.aircraft-atlas.v2"
AXES=[
    ("speed","source_predicted_top_speed_bps","blocks/s","SOURCE_MICROKERNEL","desc","Source-predicted speed"),
    ("yaw","yaw_change_20t_deg","deg/20t","SOURCE_MICROKERNEL","desc","Yaw response / 20t"),
    ("pitch","pitch_change_20t_deg","deg/20t","SOURCE_MICROKERNEL","desc","Pitch response / 20t"),
    ("same_input_retention","turn_exit_speed_retention","ratio","SOURCE_MICROKERNEL_IDENTICAL_INPUT","desc","20t same-input speed retention"),
    ("turn_90_ticks","ticks_to_90_yaw","ticks","SOURCE_MICROKERNEL_EQUAL_ANGLE","asc","Ticks to 90° yaw"),
    ("equal_angle_retention","equal_angle_90_speed_retention","ratio","SOURCE_MICROKERNEL_EQUAL_ANGLE","desc","90° equal-angle speed retention"),
    ("distance_90","distance_to_90_yaw_blocks","blocks","SOURCE_MICROKERNEL_EQUAL_ANGLE","asc","Distance travelled to 90° yaw"),
    ("durability","durability","normalized","SOURCE_DIRECT","desc","Durability"),
]
LABELS={a[0]:a[5] for a in AXES}

def load(path: Path) -> list[dict]:
    with path.open("r",encoding="utf-8",newline="") as handle:
        rows=list(csv.DictReader(handle))
    if len(rows)!=24 or len({r["aircraft_id"] for r in rows})!=24:
        raise ValueError("Atlas must contain exactly 24 unique aircraft")
    if {r["schema_version"] for r in rows}!={SOURCE_SCHEMA}:
        raise ValueError("Expected source Atlas v2")
    numeric={a[1] for a in AXES}
    for row in rows:
        for col in numeric:
            row[col]=float(row[col])
    return rows

def quantile(values:list[float],p:float)->float:
    values=sorted(values); pos=(len(values)-1)*p; lo,hi=math.floor(pos),math.ceil(pos)
    return values[lo] if lo==hi else values[lo]+(values[hi]-values[lo])*(pos-lo)

def ordered(rows:list[dict],axis:tuple)->list[dict]:
    _,col,_,_,direction,_=axis
    return sorted(rows,key=lambda r:((-r[col]) if direction=="desc" else r[col],r["aircraft_id"]))

def iqr_view(rows:list[dict],col:str)->dict:
    values=[r[col] for r in rows]; q1,q3=quantile(values,.25),quantile(values,.75)
    iqr=q3-q1; low,high=q1-1.5*iqr,q3+1.5*iqr
    return {"method":"inclusive_quartiles_1.5_iqr","q1":q1,"q3":q3,"low_fence":low,"high_fence":high,
      "flags":[{"aircraft_id":r["aircraft_id"],"value":r[col]} for r in rows if r[col]<low or r[col]>high]}

def build(rows:list[dict])->dict:
    n=len(rows); quartile_bucket=math.ceil(n*.25); ranks={}; axes={}
    for axis in AXES:
        key,col,unit,evidence,direction,_=axis; order=ordered(rows,axis)
        ranks[key]={r["aircraft_id"]:i+1 for i,r in enumerate(order)}
        axes[key]={
          "field":col,"unit":unit,"evidence":evidence,
          "ranking_direction":"higher_value_first" if direction=="desc" else "lower_value_first",
          "best":{"aircraft_id":order[0]["aircraft_id"],"value":order[0][col]},
          "worst":{"aircraft_id":order[-1]["aircraft_id"],"value":order[-1][col]},
          "top5":[{"rank":i+1,"aircraft_id":r["aircraft_id"],"value":r[col]} for i,r in enumerate(order[:5])],
          "bottom5":[{"rank":n-4+i,"aircraft_id":r["aircraft_id"],"value":r[col]} for i,r in enumerate(order[-5:])],
          "iqr_flagging":iqr_view(rows,col)}
    doctrines={}
    for doctrine in sorted({r["doctrine"] for r in rows}):
        group=[r for r in rows if r["doctrine"]==doctrine]; metrics={}
        for axis in AXES:
            key,col,_,_,_,_=axis; order=ordered(group,axis); values=[r[col] for r in group]
            metrics[key]={
              "best":{"aircraft_id":order[0]["aircraft_id"],"value":order[0][col]},
              "worst":{"aircraft_id":order[-1]["aircraft_id"],"value":order[-1][col]},
              "min_value":min(values),"max_value":max(values),"median":statistics.median(values),"spread":max(values)-min(values),
              "iqr_flagging":iqr_view(group,col) if len(group)>=4 else {"status":"NOT_EVALUATED_GROUP_LT_4"}}
        doctrines[doctrine]={"count":len(group),"metrics":metrics}
    aircraft=[]
    for row in sorted(rows,key=lambda r:r["aircraft_id"]):
        group=[r for r in rows if r["doctrine"]==row["doctrine"]]
        global_ranks={key:ranks[key][row["aircraft_id"]] for key,_,_,_,_,_ in AXES}
        doctrine_ranks={key:next(i+1 for i,r in enumerate(ordered(group,axis)) if r["aircraft_id"]==row["aircraft_id"])
                        for axis in AXES for key in [axis[0]]}
        flags=[]
        if global_ranks["yaw"]<=quartile_bucket and global_ranks["same_input_retention"]>n-quartile_bucket:
            flags.append("HIGH_YAW_LOW_SAME_INPUT_RETENTION")
        if global_ranks["same_input_retention"]<=quartile_bucket and global_ranks["yaw"]>n-quartile_bucket:
            flags.append("HIGH_SAME_INPUT_RETENTION_LOW_YAW")
        if global_ranks["turn_90_ticks"]<=quartile_bucket and global_ranks["equal_angle_retention"]>n-quartile_bucket:
            flags.append("FAST_90_LOW_EQUAL_ANGLE_RETENTION")
        if global_ranks["equal_angle_retention"]<=quartile_bucket and global_ranks["turn_90_ticks"]>n-quartile_bucket:
            flags.append("SLOW_90_HIGH_EQUAL_ANGLE_RETENTION")
        aircraft.append({"aircraft_id":row["aircraft_id"],"base_id":row["base_id"],"role":row["role"],"faction":row["faction"],
          "doctrine":row["doctrine"],"features":{key:row[col] for key,col,_,_,_,_ in AXES},
          "global_ranks":global_ranks,"doctrine_ranks":doctrine_ranks,"query_flags":flags,"evidence":row["evidence"]})
    return {"schema_version":SCHEMA,"source_atlas_schema":SOURCE_SCHEMA,
      "status":"SOURCE_MICROKERNEL_ONLY_REAL_RUNTIME_CALIBRATION_PENDING","aircraft_count":n,"quartile_bucket_size":quartile_bucket,
      "method_notes":[
        "Ranks are per-axis only; no composite strongest-aircraft score is calculated.",
        "same_input_retention compares speed after the same 20-tick full-yaw command.",
        "equal_angle_retention compares speed after each aircraft actually achieves 90 degrees of yaw.",
        "turn_90_ticks and distance_90 rank lower values first; lower distance is descriptive and is not asserted to be an aerodynamic turn radius.",
        "IQR flags are statistical inspection hints, not physics anomalies or causal findings.",
        "Real-runtime performance remains pending same-artifact calibration."],
      "axes":axes,"doctrines":doctrines,"aircraft":aircraft}

def fmt(key:str,value:float)->str:
    if key=="durability": return f"{value:.2f}"
    if key=="turn_90_ticks": return str(round(value))
    return f"{value:.6f}"

def markdown(view:dict)->str:
    lines=["# Warfare Wings Aircraft Atlas — 24 Base Aircraft (v2)","",
      "> Status: **SOURCE MICROKERNEL ONLY / SAME-ARTIFACT MINECRAFT CALIBRATION PENDING.**",
      "> Same-input and equal-angle turn metrics are intentionally separate. No composite “best aircraft” score is calculated.","",
      "## Global extrema","",
      "| Axis | Best / highest-priority end | Value | Opposite end | Value | Rank direction | Evidence |",
      "|---|---|---:|---|---:|---|---|"]
    for key,_,_,_,_,label in AXES:
        a=view["axes"][key]
        lines.append(f"| {label} | `{a['best']['aircraft_id']}` | {fmt(key,a['best']['value'])} | `{a['worst']['aircraft_id']}` | {fmt(key,a['worst']['value'])} | `{a['ranking_direction']}` | `{a['evidence']}` |")
    lines += ["","## Why the two retention axes differ","",
      "- `same_input_retention`: speed retained after every aircraft receives the same full-yaw input for 20 ticks.",
      "- `equal_angle_retention`: speed retained when each aircraft has actually changed yaw by 90°.",
      "- A slow-turning aircraft can score high on both retention metrics, but `turn_90_ticks` and `distance_90` expose the time/space cost of achieving that turn.","",
      "### Representative equal-angle results","",
      "| Aircraft | 90° ticks | 90° retention | Distance to 90° | 20t yaw |","|---|---:|---:|---:|---:|"]
    by_id={a["aircraft_id"]:a for a in view["aircraft"]}
    for aid in ("warfare_wings:il2","warfare_wings:a6m","warfare_wings:spitfire","warfare_wings:yak3","warfare_wings:ki84","warfare_wings:p47n","warfare_wings:b17"):
        a=by_id[aid]["features"]
        lines.append(f"| `{aid}` | {a['turn_90_ticks']:.0f} | {a['equal_angle_retention']:.6f} | {a['distance_90']:.3f} | {a['yaw']:.3f}° |")
    lines += ["","## Doctrine contrasts","",
      "These are within-label ranges, not claims that the doctrine label itself caused the difference.","",
      "| Doctrine | N | 90° turn time | Equal-angle retention | Speed | Durability |",
      "|---|---:|---|---|---|---|"]
    def rng(d,key):
        m=d["metrics"][key]
        return f"`{m['best']['aircraft_id']}` {fmt(key,m['best']['value'])} ↔ `{m['worst']['aircraft_id']}` {fmt(key,m['worst']['value'])}"
    for doctrine in ("turn_fighter","energy_fighter","attacker","escort"):
        d=view["doctrines"][doctrine]
        lines.append(f"| `{doctrine}` | {d['count']} | {rng(d,'turn_90_ticks')} | {rng(d,'equal_angle_retention')} | {rng(d,'speed')} | {rng(d,'durability')} |")
    lines += ["","## High-value contrasts for AI design","",
      "- **A6M:** 90° in 42 ticks, fastest of the three `turn_fighter` aircraft, but it also has the lowest equal-angle retention of all 24 (0.925567). Its advantage is rapid nose change, not low-cost turning.",
      "- **Spitfire / Yak-3:** 44 / 46 ticks to 90° with 0.935021 / 0.939018 retention. They trade a little nose speed for less speed loss than A6M.",
      "- **P-47N:** 60 ticks to 90° and 0.964626 retention while remaining the fastest source-speed aircraft. Inside `energy_fighter` it is slowest to rotate to 90° but best at equal-angle speed retention.",
      "- **Ki-84:** 48 ticks to 90° versus P-47N's 60, but 0.941936 retention. This quantitatively separates a tighter energy fighter from a more extension-oriented one.",
      "- **IL-2:** fastest 90° yaw result across all 24 at 41 ticks, reinforcing that attacker role does not imply low nose authority.",
      "- **Ju 87:** 81 ticks to 90° with 0.983141 retention. Compared with IL-2, the same attacker label spans a very different control/time envelope.",
      "- **B-17:** takes 118 ticks to reach 90° but still retains 0.994638 speed. Equal-angle normalization confirms low speed loss, while turn time shows the major tactical cost.",
      "- **G4M:** reaches 90° in 53 ticks, far faster than B-17/B-29/G10N/He111 members of the `escort` group, so that label is not a single maneuver profile.",
      "- **G10N1 vs G10N2:** remain identical in this wind-off Atlas despite mass 22 vs 17, consistent with mass not acting as ordinary yaw/pitch inertia in the inspected IA 1.3.3 path.","",
      "## Statistical inspection flags",""]
    total=sum(len(a["iqr_flagging"]["flags"]) for a in view["axes"].values())
    lines += [f"Global 1.5×IQR flag count across the eight Atlas axes: **{total}**.","",
      "Within-doctrine flags (groups with at least 4 aircraft):"]
    found=0
    for doctrine,d in view["doctrines"].items():
        for key,m in d["metrics"].items():
            for flag in m["iqr_flagging"].get("flags",[]):
                found+=1; lines.append(f"- `{doctrine}` / `{key}`: `{flag['aircraft_id']}` = {flag['value']:.9f} (`STATISTICAL_IQR_FLAG`).")
    if not found: lines.append("- none")
    lines += ["","The 3-aircraft `turn_fighter` group is not IQR-tested because the sample is too small.","",
      "## Query flags","",
      "Query flags use global top/bottom quartile membership (6 of 24 aircraft per quartile). They are routing hints, not overall combat rankings.","",
      "- `HIGH_YAW_LOW_SAME_INPUT_RETENTION` / `HIGH_SAME_INPUT_RETENTION_LOW_YAW`: fixed-duration contrast.",
      "- `FAST_90_LOW_EQUAL_ANGLE_RETENTION`: fast 90° completion paired with bottom-quartile equal-angle retention.",
      "- `SLOW_90_HIGH_EQUAL_ANGLE_RETENTION`: slow 90° completion paired with top-quartile equal-angle retention.","",
      "## Interpretation boundary","",
      "The equal-angle metrics repair an important comparison problem, but they are still source-microkernel results. Same-artifact Minecraft trace calibration remains the promotion gate before any axis is labeled `MEASURED`.",""]
    return "\n".join(lines)

def canonical_json_numbers(value):
    if isinstance(value,float) and value.is_integer(): return int(value)
    if isinstance(value,list): return [canonical_json_numbers(v) for v in value]
    if isinstance(value,dict): return {k:canonical_json_numbers(v) for k,v in value.items()}
    return value

def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("atlas_csv",type=Path); p.add_argument("--json",type=Path,required=True); p.add_argument("--markdown",type=Path,required=True)
    args=p.parse_args(); view=build(load(args.atlas_csv)); args.json.parent.mkdir(parents=True,exist_ok=True); args.markdown.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(canonical_json_numbers(view),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    args.markdown.write_text(markdown(view),encoding="utf-8")
    print(f"built AI Atlas v2 for {view['aircraft_count']} aircraft")
if __name__=="__main__": main()
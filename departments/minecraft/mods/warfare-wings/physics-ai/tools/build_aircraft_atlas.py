#!/usr/bin/env python3
"""Build AI-readable and human-readable views from the 24-aircraft source Atlas.

The builder does not create a composite "best aircraft" score. Each axis is ranked independently.
Retention is explicitly the speed ratio after an identical 20-tick full-yaw command and must not be
misread as equal-angle turn efficiency.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from pathlib import Path

SCHEMA = "ww.physics.aircraft-atlas-ai.v1"
AXES = [
    ("speed","source_predicted_top_speed_bps","blocks/s","SOURCE_MICROKERNEL"),
    ("yaw","yaw_change_20t_deg","deg/20t","SOURCE_MICROKERNEL"),
    ("pitch","pitch_change_20t_deg","deg/20t","SOURCE_MICROKERNEL"),
    ("retention","turn_exit_speed_retention","ratio","SOURCE_MICROKERNEL_IDENTICAL_INPUT"),
    ("durability","durability","normalized","SOURCE_DIRECT"),
]
LABELS = {
    "speed":"Source-predicted speed",
    "yaw":"Yaw response / 20t",
    "pitch":"Pitch response / 20t",
    "retention":"20t identical-input speed retention",
    "durability":"Durability",
}

def load(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 24 or len({r["aircraft_id"] for r in rows}) != 24:
        raise ValueError("Atlas must contain exactly 24 unique aircraft")
    numeric = {col for _,col,_,_ in AXES}
    for row in rows:
        for col in numeric:
            row[col] = float(row[col])
    return rows

def quantile(values: list[float], p: float) -> float:
    values = sorted(values)
    pos = (len(values)-1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return values[lo]
    return values[lo] + (values[hi]-values[lo]) * (pos-lo)

def rank(rows: list[dict], col: str) -> list[dict]:
    return sorted(rows, key=lambda r: (-r[col], r["aircraft_id"]))

def iqr_view(rows: list[dict], col: str) -> dict:
    values = [r[col] for r in rows]
    q1, q3 = quantile(values, .25), quantile(values, .75)
    iqr = q3-q1
    low, high = q1-1.5*iqr, q3+1.5*iqr
    return {
        "method":"inclusive_quartiles_1.5_iqr",
        "q1":q1, "q3":q3, "low_fence":low, "high_fence":high,
        "flags":[{"aircraft_id":r["aircraft_id"],"value":r[col]}
                 for r in rows if r[col] < low or r[col] > high],
    }

def build(rows: list[dict]) -> dict:
    n=len(rows)
    quartile_bucket=math.ceil(n*.25)
    ranks={}
    axes={}
    for key,col,unit,evidence in AXES:
        ordered=rank(rows,col)
        ranks[key]={r["aircraft_id"]:i+1 for i,r in enumerate(ordered)}
        axes[key]={
            "field":col, "unit":unit, "evidence":evidence,
            "ranking_direction":"higher_value_first",
            "max":{"aircraft_id":ordered[0]["aircraft_id"],"value":ordered[0][col]},
            "min":{"aircraft_id":ordered[-1]["aircraft_id"],"value":ordered[-1][col]},
            "top5":[{"rank":i+1,"aircraft_id":r["aircraft_id"],"value":r[col]}
                    for i,r in enumerate(ordered[:5])],
            "bottom5":[{"rank":n-4+i,"aircraft_id":r["aircraft_id"],"value":r[col]}
                       for i,r in enumerate(ordered[-5:])],
            "iqr_flagging":iqr_view(rows,col),
        }

    doctrines={}
    for doctrine in sorted({r["doctrine"] for r in rows}):
        group=[r for r in rows if r["doctrine"] == doctrine]
        metrics={}
        for key,col,_,_ in AXES:
            ordered=rank(group,col)
            values=[r[col] for r in group]
            view={
                "max":{"aircraft_id":ordered[0]["aircraft_id"],"value":ordered[0][col]},
                "min":{"aircraft_id":ordered[-1]["aircraft_id"],"value":ordered[-1][col]},
                "median":statistics.median(values),
                "spread":max(values)-min(values),
            }
            view["iqr_flagging"] = iqr_view(group,col) if len(group) >= 4 else {"status":"NOT_EVALUATED_GROUP_LT_4"}
            metrics[key]=view
        doctrines[doctrine]={"count":len(group),"metrics":metrics}

    aircraft=[]
    for row in sorted(rows,key=lambda r:r["aircraft_id"]):
        global_ranks={key:ranks[key][row["aircraft_id"]] for key,_,_,_ in AXES}
        group=[r for r in rows if r["doctrine"] == row["doctrine"]]
        doctrine_ranks={}
        for key,col,_,_ in AXES:
            doctrine_ranks[key]=next(i+1 for i,r in enumerate(rank(group,col)) if r["aircraft_id"] == row["aircraft_id"])
        flags=[]
        if global_ranks["speed"] <= quartile_bucket and global_ranks["yaw"] > n-quartile_bucket:
            flags.append("HIGH_SPEED_LOW_YAW")
        if global_ranks["speed"] > n-quartile_bucket and global_ranks["yaw"] <= quartile_bucket:
            flags.append("LOW_SPEED_HIGH_YAW")
        if global_ranks["yaw"] <= quartile_bucket and global_ranks["retention"] > n-quartile_bucket:
            flags.append("HIGH_YAW_LOW_RETENTION")
        if global_ranks["retention"] <= quartile_bucket and global_ranks["yaw"] > n-quartile_bucket:
            flags.append("HIGH_RETENTION_LOW_YAW")
        aircraft.append({
            "aircraft_id":row["aircraft_id"], "base_id":row["base_id"],
            "role":row["role"], "faction":row["faction"], "doctrine":row["doctrine"],
            "features":{key:row[col] for key,col,_,_ in AXES},
            "global_ranks":global_ranks, "doctrine_ranks":doctrine_ranks,
            "query_flags":flags, "evidence":row["evidence"],
        })
    return {
        "schema_version":SCHEMA,
        "status":"SOURCE_MICROKERNEL_ONLY_REAL_RUNTIME_CALIBRATION_PENDING",
        "aircraft_count":n,
        "quartile_bucket_size":quartile_bucket,
        "method_notes":[
            "Ranks are per-axis only; no composite strongest-aircraft score is calculated.",
            "Retention is speed ratio after the same 20-tick full-yaw input, not energy loss normalized by achieved turn angle.",
            "IQR flags are statistical inspection hints, not physics anomalies or causal findings.",
            "Real-runtime performance remains pending same-artifact calibration.",
        ],
        "axes":axes, "doctrines":doctrines, "aircraft":aircraft,
    }

def markdown(view: dict) -> str:
    lines=[
        "# Warfare Wings Aircraft Atlas — 24 Base Aircraft","",
        "> Status: **SOURCE MICROKERNEL ONLY / SAME-ARTIFACT MINECRAFT CALIBRATION PENDING.**",
        "> No composite “best aircraft” score is calculated.","",
        "## Global extrema","",
        "| Axis | Highest | Value | Lowest | Value | Evidence |",
        "|---|---|---:|---|---:|---|",
    ]
    for key in ("speed","yaw","pitch","retention","durability"):
        a=view["axes"][key]
        digits=2 if key=="durability" else 6
        lines.append(f"| {LABELS[key]} | `{a['max']['aircraft_id']}` | {a['max']['value']:.{digits}f} | `{a['min']['aircraft_id']}` | {a['min']['value']:.{digits}f} | `{a['evidence']}` |")
    lines += ["","## Top-five lookup",""]
    for key in ("speed","yaw","pitch","retention","durability"):
        values=", ".join(f"{x['rank']}. `{x['aircraft_id']}` ({x['value']:.6f})" for x in view["axes"][key]["top5"])
        lines.append(f"- **{LABELS[key]}:** {values}")
    lines += ["","## Doctrine contrasts","",
      "These are within-label ranges, not claims that the doctrine label itself caused the difference.","",
      "| Doctrine | N | Speed range | Yaw range | Retention range | Durability range |",
      "|---|---:|---|---|---|---|"]
    def rng(d: dict, key: str, digits: int) -> str:
        m=d["metrics"][key]
        return f"`{m['min']['aircraft_id']}` {m['min']['value']:.{digits}f} → `{m['max']['aircraft_id']}` {m['max']['value']:.{digits}f}"
    for doctrine in ("turn_fighter","energy_fighter","attacker","escort"):
        d=view["doctrines"][doctrine]
        lines.append(f"| `{doctrine}` | {d['count']} | {rng(d,'speed',3)} | {rng(d,'yaw',3)} | {rng(d,'retention',6)} | {rng(d,'durability',2)} |")
    lines += ["","## High-value contrasts for AI design","",
      "- **P-47N:** globally fastest source tendency (45.791 b/s), but lowest yaw and pitch response inside `energy_fighter`; it also has that doctrine's highest identical-input retention. This supports a larger extension/re-entry envelope rather than copying a tighter energy-fighter policy.",
      "- **Ki-84:** tied near the top of source speed (44.893 b/s) while leading `energy_fighter` yaw/pitch response; its 20-tick identical-input retention is the lowest in that doctrine. A single P-47-style policy would erase this difference.",
      "- **A6M / Spitfire / Yak-3:** all are `turn_fighter`, but A6M has the highest yaw/pitch response and much lower source speed, while Yak-3 has the highest source speed of the three. The label is not a full flight profile.",
      "- **IL-2:** has the highest yaw response of all 24 aircraft despite being an attacker. Historical role stereotypes must not override runtime control values.",
      "- **Ju 87 vs IL-2:** both are `attacker`, yet Ju 87 is the slowest/lowest-yaw attacker while IL-2 is the highest-yaw/highest-durability attacker. Mission-specific attack logic needs aircraft parameters, not only the shared doctrine string.",
      "- **G4M:** is the fastest and highest-yaw member of the `escort` group. Its retention is the only within-doctrine 1.5×IQR statistical flag in the five Atlas axes; this is an inspection hint, not a physics anomaly.",
      "- **G10N1 vs G10N2:** they have identical source-microkernel Atlas features even though raw mass differs (22 vs 17). In this wind-off baseline that is expected: mass is not ordinary yaw/pitch inertia in the inspected IA 1.3.3 path.",
      "- **B-17/B-29:** very high 20-tick retention accompanies very low achieved yaw/pitch. That metric is therefore not “turning efficiency”; it is speed retained under the same control input and must later be complemented by an equal-angle turn test.",
      "","## Statistical inspection flags",""]
    global_flags=sum(len(a["iqr_flagging"]["flags"]) for a in view["axes"].values())
    lines += [f"Global 1.5×IQR flag count across the five Atlas axes: **{global_flags}**.","",
              "Within-doctrine flags (groups with at least 4 aircraft):"]
    found=0
    for doctrine,d in view["doctrines"].items():
        for key,m in d["metrics"].items():
            flags=m["iqr_flagging"].get("flags",[])
            for flag in flags:
                found += 1
                lines.append(f"- `{doctrine}` / `{key}`: `{flag['aircraft_id']}` = {flag['value']:.9f} (`STATISTICAL_IQR_FLAG`).")
    if not found:
        lines.append("- none")
    lines += ["",
      "The 3-aircraft `turn_fighter` group is not IQR-tested because the sample is too small.","",
      "## Query flags","",
      "Query flags use global top/bottom quartile membership (6 of 24 aircraft per quartile). They are routing hints, not rankings of overall combat strength.","",
      "- `HIGH_YAW_LOW_RETENTION`: top-quartile yaw response + bottom-quartile identical-input retention.",
      "- `HIGH_RETENTION_LOW_YAW`: top-quartile identical-input retention + bottom-quartile yaw response.",
      "- `HIGH_SPEED_LOW_YAW` / `LOW_SPEED_HIGH_YAW`: reserved for the corresponding speed/yaw quartile contrasts; none are present in this Atlas revision.","",
      "## Interpretation boundary","",
      "The Atlas is deliberately source-faithful and explainable, but it is **not yet measured same-artifact performance**. The first real-runtime calibration remains A6M `a6m-throttle-step-v1`. Once that trace arrives, the same calibration method will determine which Atlas axes can be promoted from `SOURCE_MICROKERNEL` toward `MEASURED` for the supplied Warfare Wings artifact.",""]
    return "\n".join(lines)

def canonical_json_numbers(value):
    """Match JSON's natural integer representation for mathematically integral floats."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [canonical_json_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_json_numbers(item) for key, item in value.items()}
    return value

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("atlas_csv",type=Path)
    parser.add_argument("--json",type=Path,required=True)
    parser.add_argument("--markdown",type=Path,required=True)
    args=parser.parse_args()
    view=build(load(args.atlas_csv))
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.markdown.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(canonical_json_numbers(view),indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    args.markdown.write_text(markdown(view),encoding="utf-8")
    print(f"built AI Atlas for {view['aircraft_count']} aircraft")

if __name__ == "__main__":
    main()
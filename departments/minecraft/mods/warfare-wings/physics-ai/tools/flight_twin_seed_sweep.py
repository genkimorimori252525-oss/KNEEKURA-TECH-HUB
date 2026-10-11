#!/usr/bin/env python3
"""Deterministic multi-seed 24-distinct-aircraft closed-loop SOURCE safety study.

The genuine pinned Minecraft/Forge GameTests remain separate and authoritative.
This runs actual Java17 Ia133Microkernel/TacticalAirAI source dynamics with
per-observer synthetic sensors, never fabricated REAL receipts or kill counts.
"""

from __future__ import annotations

import argparse
import csv
from html import escape
import json
import math
from pathlib import Path
import tempfile

from flight_lab_run import compile_lab, get_java17, run_twin

SCHEMA = "ww.flight-twin.multi-seed-source-safety.v1"
PAIR_COUNT = 24 * 23 // 2
EXPECTED_SHA = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
FIELDS = (
    "seed", "ticks", "simultaneous_aircraft", "source_physics_updates",
    "min_swept_pair_blocks", "swept_pair_breaches_lt6",
    "closest_pair_a", "closest_pair_b", "closest_pair_tick",
    "min_b17_hostile_blocks", "b17_intrusion_ticks_within95",
    "first_b17_intrusion_tick", "safety_status", "failed_gates",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing SOURCE scientific CSV fields: {path}")
        rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Incomplete SOURCE scientific CSV rows: {path}")
    return rows


def _number(value: str | int | float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite SOURCE safety measurement: {label}")
    return number


def verify_one(seed: int, ticks: int, source: dict, directory: Path) -> dict:
    """Independently reconcile a returned Java source run to every pair row."""
    if (source.get("schema") != "ww.flight-twin.closed-loop.v1"
            or source.get("aircraft_anchor_sha256") != EXPECTED_SHA
            or "NO_FORGE_PARITY" not in source.get("evidence", "")
            or source.get("body_separation_radius_blocks") != 6
            or source.get("b17_protection_radius_blocks") != 95
            or source.get("scenario_count") != 1
            or str(source.get("seed")) != str(seed)):
        raise ValueError("SOURCE result identity, pinned anchor or 6b/95b safety gate changed")
    case = source["scenarios"][0]
    if (case["id"] != "all_24_unique" or case["simulated_ticks"] != ticks
            or case["active_aircraft"] != 24 or case["unique_aircraft_types"] != 24
            or case["total_ai_decisions"] != 24 * ticks
            or case["simultaneous_source_updates"] != 24 * ticks
            or source["simulated_source_ticks"] != 24 * ticks):
        raise ValueError("Missing actual 24-aircraft simultaneous source dynamics")
    pairs = _read_csv(directory / "twin_pairs.csv")
    assets = _read_csv(directory / "twin_assets.csv")
    if len(pairs) != PAIR_COUNT or len(assets) != 1 or assets[0]["asset_unit"] != "type-b17":
        raise ValueError("Missing independent 276 pairs or actual moving B-17")
    ids = set()
    pair_min = math.inf
    worst = None
    pair_breaches = 0
    for pair in pairs:
        if pair["scenario"] != "all_24_unique":
            raise ValueError("Unexpected source scenario in pair report")
        key = tuple(sorted((pair["first_unit"], pair["second_unit"])))
        if len(set(key)) != 2 or key in ids:
            raise ValueError("Duplicate/invalid pair identity")
        ids.add(key)
        separation = _number(pair["min_swept_center_separation_blocks"], str(key))
        violations = int(pair["swept_lt6_ticks"])
        if violations < 0 or violations > ticks:
            raise ValueError("Invalid actual SOURCE pair violation count")
        breached = separation < 6 or violations > 0
        if pair["body_gate"] != ("FAILED" if breached else "PASS"):
            raise ValueError("Pair violation mislabeled as safety pass")
        pair_breaches += violations
        if separation < pair_min:
            pair_min = separation
            worst = pair
    if (abs(pair_min-case["min_swept_pair_separation_blocks"]) > 1e-6
            or pair_breaches != case["swept_lt6_pair_ticks"]):
        raise ValueError("24-aircraft source headline contradicts pair measurements")
    asset = assets[0]
    if (asset["scenario"] != "all_24_unique"
            or _number(asset["protection_radius_blocks"], "radius") != 95):
        raise ValueError("B-17 protected asset or 95b gate swapped")
    intrusion = int(asset["within95_swept_ticks"])
    if intrusion < 0 or intrusion > ticks or intrusion != case["swept_within95_hostile_ticks"]:
        raise ValueError("Source B-17 intrusion count contradicts independent asset rows")
    first_intrusion = int(asset["first_intrusion_swept_tick"])
    if (intrusion == 0 and first_intrusion != -1
            or intrusion > 0 and not 1 <= first_intrusion <= ticks):
        raise ValueError("Source intrusion time inconsistent with physical events")
    if asset["protection_gate"] != ("FAILED" if intrusion else "PASS"):
        raise ValueError("Unsafe SOURCE B-17 asset spoofed as protected")
    unsafe = pair_breaches > 0 or intrusion > 0 or bool(case["failed_operational_gates"])
    expected = "FAILED_SOURCE_SAFETY" if unsafe else "PASS_SOURCE_SAFETY"
    if case["status"] != expected:
        raise ValueError("SOURCE operational failed gate was suppressed")
    return {
        "seed": seed, "ticks": ticks,
        "simultaneous_aircraft": 24,
        "source_physics_updates": 24 * ticks,
        "min_swept_pair_blocks": round(pair_min, 9),
        "swept_pair_breaches_lt6": pair_breaches,
        "closest_pair_a": worst["first_unit"],
        "closest_pair_b": worst["second_unit"],
        "closest_pair_tick": int(worst["closest_swept_tick"]),
        "min_b17_hostile_blocks": round(
            _number(asset["min_swept_hostile_blocks"], "B-17 nearest enemy"), 9),
        "b17_intrusion_ticks_within95": intrusion,
        "first_b17_intrusion_tick": first_intrusion,
        "safety_status": expected,
        "failed_gates": "|".join(case["failed_operational_gates"]),
    }


def summarize(rows: list[dict], first_seed: int, step: int) -> dict:
    if not rows:
        raise ValueError("No experiments executed")
    count = len(rows)
    total = sum(row["source_physics_updates"] for row in rows)
    pair_unsafe = [r for r in rows if r["swept_pair_breaches_lt6"]]
    asset_unsafe = [r for r in rows if r["b17_intrusion_ticks_within95"]]
    return {
        "schema": SCHEMA,
        "evidence": "24_ACTUAL_CONCURRENT_SOURCE_PHYSICS__NOT_REAL_MINECRAFT__NO_FORGE_PARITY",
        "source_anchor_sha256": EXPECTED_SHA,
        "source_seed_start": first_seed,
        "source_seed_step": step,
        "seed_count": count,
        "unique_airframes_per_seed": 24,
        "fixed_safety_gates": {"min_pair_blocks": 6, "b17_protection_blocks": 95},
        "total_source_physics_updates": total,
        "pair_lt6_failed_seed_count": len(pair_unsafe),
        "b17_intrusion_failed_seed_count": len(asset_unsafe),
        "total_pair_violation_ticks": sum(r["swept_pair_breaches_lt6"] for r in rows),
        "total_b17_intrusion_ticks": sum(r["b17_intrusion_ticks_within95"] for r in rows),
        "min_pair_separation_across_seeds": min(r["min_swept_pair_blocks"] for r in rows),
        "min_b17_hostile_separation_across_seeds": min(r["min_b17_hostile_blocks"] for r in rows),
        "full_mission_success_seeds": sum(r["safety_status"] == "PASS_SOURCE_SAFETY" for r in rows),
        "failed_mission_seeds": sum(r["safety_status"] == "FAILED_SOURCE_SAFETY" for r in rows),
        "limitations": [
            "Every trial advances all 24 distinct planes through 20Hz SOURCE microkernel physics",
            "No real Forge voxel collision, server weapons, damage, kills or landing completion",
            "Each seed varies the predeclared initial conditions without altering 6b/95b gates",
            "A software batch completing does not turn failed mission cases into PASS",
        ],
    }


def write_html(output: Path, summary: dict, rows: list[dict]) -> None:
    """One portable, independently labeled SOURCE risk heatmap.

    Each link reaches locally generated SOURCE experiments, not Minecraft
    recordings. The page requires no web, scripts, CSS or installed service.
    """
    if not rows or len(rows) != summary["seed_count"]:
        raise ValueError("Unmatched SOURCE seed-sweep visualization inputs")
    markers = []
    table = []
    for index, data in enumerate(rows):
        seed = int(data["seed"])
        collisions = int(data["swept_pair_breaches_lt6"])
        intrusions = int(data["b17_intrusion_ticks_within95"])
        risk_style = "#b54a42" if collisions else "#567d70"
        x = 42 + index * 895 / max(1, len(rows)-1)
        y = 230 - intrusions * 195 / max(1, int(rows[0]["ticks"]))
        markers.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{5 if collisions else 3}" '
            f'fill="{risk_style}"><title>'
            f'SEED {seed} | B17 intrusions {intrusions} | pair danger ticks {collisions}'
            '</title></circle>')
        table.append(
            '<tr>'
            f'<td><a href="seed-{seed}/twin_summary.json">{seed}</a></td>'
            f'<td class="right">{data["min_swept_pair_blocks"]:.3f}</td>'
            f'<td class="right" style="color:{risk_style};font-weight:600">{collisions}</td>'
            f'<td class="right">{intrusions}</td>'
            f'<td>{escape(str(data["closest_pair_a"]))} vs '
            f'{escape(str(data["closest_pair_b"]))}</td>'
            f'<td class="right">{int(data["closest_pair_tick"])}</td>'
            f'<td>{escape(str(data["safety_status"]))}</td></tr>')
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>24 Aircraft SOURCE Safety / {len(rows)} Seed Sweep</title>
<style>
:root{{font-family:system-ui,Segoe UI,sans-serif;color:#263544;background:#f5f7f8}}
body{{margin:0 auto;max-width:1100px;padding:28px}}
.sub{{color:#657486;font-size:14px}} .metrics{{display:flex;gap:12px;flex-wrap:wrap}}
.metric{{background:white;padding:15px 22px;border:1px solid #d6dce0;border-radius:8px}}
.metric strong{{display:block;font-size:25px}} .risk{{color:#b54a42}}
section{{margin-top:20px;padding:16px;background:white;border:1px solid #d6dce0;border-radius:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{padding:8px 5px;text-align:left;border-bottom:1px solid #e4e9ec}}
th{{position:sticky;top:0;background:#f5f7f8}} .right{{text-align:right}}
a{{color:#245f83}} svg{{width:100%;height:auto}}
</style></head><body>
<h1>24 Aircraft · Independent-Seed SOURCE Flight Safety</h1>
<p class="sub">Evidence: {escape(summary["evidence"])}. This is Java17
closed-loop synthetic-sensor physics; it is <b>NOT original Minecraft/Forge
evidence</b>. All 24 original identities undergo genuine SOURCE physics at
20 Hz for each seed. Strict 6-block pair/95-block B-17 gates stay unchanged.</p>
<div class="metrics">
<div class="metric"><strong>{len(rows)}</strong> distinct seeds</div>
<div class="metric"><strong>{summary["total_source_physics_updates"]:,}</strong> SOURCE physics steps</div>
<div class="metric"><strong class="risk">{summary["pair_lt6_failed_seed_count"]}</strong> seeds with under-6b proximity</div>
<div class="metric"><strong class="risk">{summary["b17_intrusion_failed_seed_count"]}</strong> seeds with B-17 intrusions</div>
<div class="metric"><strong>{summary["min_pair_separation_across_seeds"]:.3f}b</strong> minimum pair clearance</div>
</div>
<section><h2>B-17 95-block intrusion by seed</h2>
<p class="sub">Points mark the counted swept-time violation ticks of each full
24-aircraft SOURCE scenario. Larger red points also violate the 6b centre
separation gate. Samples do not claim projectile hits or successful missions.</p>
<svg viewBox="0 0 980 270" role="img" aria-label="SOURCE B17 intrusion ticks per seed">
<line x1="42" y1="230" x2="942" y2="230" stroke="#657486"/>
<line x1="42" y1="20" x2="42" y2="230" stroke="#657486"/>
<text x="42" y="258" font-size="12">First seed: {rows[0]["seed"]}</text>
<text x="772" y="258" font-size="12">Last seed: {rows[-1]["seed"]}</text>
<text x="46" y="19" font-size="12">B-17 within 95b [ticks]</text>
{''.join(markers)}
</svg></section>
<section><h2>Every result, including FAILED cases</h2>
<p class="sub">Links open the <i>source-only</i> per-seed JSON from this same
portable directory. All per-seed trajectory/control CSV files are retained
alongside it; no original owner JAR or runtime CSV is packaged.</p>
<div style="max-height:650px;overflow:auto"><table><thead>
<tr><th>Seed / SOURCE JSON</th><th class="right">Min pair b</th>
<th class="right">Under6 ticks</th><th class="right">B-17 within95</th>
<th>Closest pair</th><th class="right">Closest tick</th><th>Mission</th></tr>
</thead><tbody>{''.join(table)}</tbody></table></div>
</section>
<p class="sub">The causal source code, JSON and CSV retain evidence categories.
This chart does not make ground collision, actual voxel LOS, stall, landing,
safe ammunition use, or real opponent death claims.</p></body></html>
"""
    (output / "seed_sweep.html").write_text(html, encoding="utf-8", newline="\n")


def run(output: Path, java_home: Path | None, first_seed: int,
        count: int, step: int, ticks: int) -> dict:
    if (count < 1 or count > 2048 or step < 1 or ticks < 20 or ticks > 2400):
        raise ValueError("Invalid bounded 24-unique-airframe source stress experiment")
    last_seed = first_seed + (count - 1) * step
    if first_seed < -(1 << 63) or last_seed >= 1 << 63:
        raise ValueError("Source seed must fit signed Java long")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Refusing to mix new stress evidence into an existing nonempty output")
    output.mkdir(parents=True, exist_ok=True)
    javac, java = get_java17(java_home)
    rows = []
    with tempfile.TemporaryDirectory(prefix="ww-24stress-classes-") as temp:
        classes = Path(temp) / "classes"
        compile_lab(javac, classes)
        for index in range(count):
            seed = first_seed + step * index
            leaf = output / f"seed-{seed}"
            source = run_twin(java, classes, leaf, seed=seed,
                              unique_ticks=ticks, trace_stride=ticks,
                              scenario="all_24_unique")
            row = verify_one(seed, ticks, source, leaf)
            rows.append(row)
            print(f"SEED_SOURCE_ONLY {seed} {row['safety_status']} "
                  f"pair_min={row['min_swept_pair_blocks']:.4f}b "
                  f"under6={row['swept_pair_breaches_lt6']} "
                  f"B17_within95={row['b17_intrusion_ticks_within95']}", flush=True)
    overview = summarize(rows, first_seed, step)
    with (output / "seed_sweep.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (output / "seed_sweep.json").write_text(
        json.dumps(overview, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    write_html(output, overview, rows)
    print(f"24_SOURCE_SEED_SWEEP_COMPLETE seeds={count} "
          f"physics_updates={overview['total_source_physics_updates']} "
          f"pair_fail_seeds={overview['pair_lt6_failed_seed_count']} "
          f"B17_fail_seeds={overview['b17_intrusion_failed_seed_count']} "
          "REAL_FORGE_PARITY_NOT_RUN", flush=True)
    return overview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--seed-start", type=int, default=20261011)
    parser.add_argument("--count", type=int, default=32)
    parser.add_argument("--seed-step", type=int, default=1)
    parser.add_argument("--ticks", type=int, default=240)
    args = parser.parse_args()
    try:
        run(args.output, args.java_home, args.seed_start, args.count,
            args.seed_step, args.ticks)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"SOURCE_24_AIRCRAFT_STRESS_FAILED: {exc}") from None


if __name__ == "__main__":
    main()

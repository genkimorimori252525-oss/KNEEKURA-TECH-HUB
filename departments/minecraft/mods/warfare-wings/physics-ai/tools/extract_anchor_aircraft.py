#!/usr/bin/env python3
"""Extract the 24 Warfare Wings base-aircraft rows from the exact user-supplied ANCHOR JAR.

This tool deliberately writes derived data only. It does not copy raw aircraft JSON or assets into
Tech Hub. The output separates raw Warfare Wings fields from Immersive Aircraft 1.3.3 effective
fields and preserves driftDrag as provenance rather than silently treating it as runtime friction.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, zipfile
from pathlib import Path

EXPECTED_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
IA_TAG = "1.3.3+1.20.1"
IA_COMMIT = "550b38d3dfdbf5cb6ec3f78468e0e60725a47605"
BASE = ["a6m","b17","b29","bf109","d4y","f4u","f6f","fw190","g10n1","g10n2","g4m","he111",
        "il2","ju87","ki61","ki84","mc202","mig3","p40e","p47n","p51d","sbd","spitfire","yak3"]
RAW = ["fuel","durability","yawSpeed","pitchSpeed","engineSpeed","pushSpeed","glideFactor",
       "driftDrag","lift","rollFactor","groundPitch","wind","mass"]
DEFAULTS = {"acceleration":1.0,"friction":0.015,"stabilizer":0.0,"groundFriction":0.95,
            "waterFriction":0.9,"rotationDecay":0.97,"horizontalDecay":0.97,"verticalDecay":0.97}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def extract(jar: Path) -> list[dict]:
    actual = digest(jar)
    if actual != EXPECTED_SHA256:
        raise ValueError(f"Unexpected Warfare Wings JAR SHA-256: {actual}")
    rows = []
    with zipfile.ZipFile(jar) as archive:
        names = set(archive.namelist())
        for base_id in BASE:
            path = f"data/warfare_wings/aircraft/{base_id}.json"
            if path not in names:
                raise ValueError(f"Missing base aircraft JSON: {path}")
            data = json.loads(archive.read(path))
            props = data["properties"]
            if set(props) != set(RAW):
                raise ValueError(f"{base_id}: unexpected property keys: {sorted(set(props) ^ set(RAW))}")
            ai = data["ai"]
            row = {
                "aircraft_id": f"warfare_wings:{base_id}", "base_id": base_id,
                "role": ai["role"], "faction": ai["faction"], "doctrine": ai["doctrine"],
                "anchor_sha256": actual,
            }
            row.update({f"raw_{key}": props[key] for key in RAW})
            row.update({f"effective_{key}": value for key, value in DEFAULTS.items()})
            for key in ("engineSpeed","yawSpeed","pitchSpeed","pushSpeed","durability","fuel",
                        "glideFactor","lift","rollFactor","groundPitch","wind","mass"):
                row[f"effective_{key}"] = props[key]
            row["driftDrag_runtime_active"] = False
            row["runtime_friction_source"] = "IA_1.3.3_default_no_friction_key"
            row["evidence"] = "ANCHOR_JAR+IA_1.3.3_SOURCE"
            rows.append(row)
    if len(rows) != 24 or len({row["aircraft_id"] for row in rows}) != 24:
        raise ValueError("24-aircraft completeness failure")
    return rows

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jar", type=Path)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    rows = extract(args.jar)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    payload = {
        "schema_version":"ww.physics.aircraft-anchor.v1",
        "anchor":{"filename":args.jar.name,"sha256":EXPECTED_SHA256},
        "ia_source_contract":{"tag":IA_TAG,"commit":IA_COMMIT,
          "runtime_friction_rule":"registered friction; default 0.015 when absent",
          "driftDrag_runtime_active_in_inspected_source":False},
        "aircraft":rows,
    }
    args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"extracted {len(rows)} base aircraft")

if __name__ == "__main__":
    main()
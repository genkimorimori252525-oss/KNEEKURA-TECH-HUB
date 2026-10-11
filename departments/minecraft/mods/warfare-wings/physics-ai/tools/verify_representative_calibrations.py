#!/usr/bin/env python3
"""Compare four real 401-sample neutral-control aircraft traces with source V3.

Requires actual Forge GameTest receipts and compiled Java 17 source classes.
Every aircraft is measured with the *same* envelope, not a historical flight
performance experiment. Reports drift, never invents a physical-parity PASS.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path

from compare_traces import compare, load_trace

AIRFRAMES = ("p47n", "spitfire", "il2", "b17")
EXPECTED_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
WINDOWS_SAFE_OUTPUT_PATH_LENGTH = 248


def _validate_windows_output_path_budget(report_dir: Path) -> None:
    """Avoid Windows MAX_PATH's silent Java-writes/Python-is_file mismatch.

    Windows can have long paths enabled for some processes but not others.
    Keep *every* generated source and comparator path under a conservative
    shared 248-character file budget, rather than trusting one JVM's exit 0.
    """
    expected = [report_dir / "representative-calibrations.json"]
    for aircraft in AIRFRAMES:
        scenario = f"{aircraft}-throttle-step-v1"
        expected.append(report_dir / f"{scenario}-reaction-source.csv")
        for name in ("calibration-summary.json", "calibration-summary.md",
                     "calibration-ai-view.json", "calibration-diff.csv"):
            expected.append(report_dir / f"{aircraft}-calibration" / name)
    longest = max(expected, key=lambda item: len(str(item)))
    if len(str(longest)) >= WINDOWS_SAFE_OUTPUT_PATH_LENGTH:
        raise ValueError(
            f"Windows MAX_PATH risk ({len(str(longest))} characters): {longest}; "
            "choose a shorter --output-dir for both Java17 and Python")


def _validate_atlas(anchor_csv: Path) -> None:
    with anchor_csv.open(encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    if len(records) != 24 or len({row["aircraft_id"] for row in records}) != 24:
        raise ValueError("Expected exactly 24 unique pinned source airframes")
    if any(row["anchor_sha256"] != EXPECTED_SHA256 for row in records):
        raise ValueError("Original owner WW anchor SHA drift")
    for airframe in AIRFRAMES:
        if sum(row["aircraft_id"] == f"warfare_wings:{airframe}" for row in records) != 1:
            raise ValueError(f"Source airframe unavailable: {airframe}")


def verify(trace_dir: Path, anchor_csv: Path, java: str, classes: Path,
           report_dir: Path) -> dict:
    # Use the identical resolved file identity for JVM output and Python input.
    # A relative report path can otherwise be sensitive to a caller's working
    # directory on the owner's Windows Forge runner.
    trace_dir = trace_dir.resolve()
    anchor_csv = anchor_csv.resolve()
    classes = classes.resolve()
    report_dir = report_dir.resolve()
    if os.name == "nt":
        _validate_windows_output_path_budget(report_dir)
    _validate_atlas(anchor_csv)
    # Check all four receipts before producing any generated output. This
    # prevents the source-only simulator from masquerading as runtime input.
    for airframe in AIRFRAMES:
        scenario = airframe + "-throttle-step-v1"
        path = trace_dir / f"{scenario}-runtime.csv"
        rows = load_trace(path, "minecraft_runtime")
        if len(rows) != 401 or rows[0]["scenario_id"] != scenario:
            raise ValueError(f"{scenario}: missing/incomplete 401-tick runtime recording")
        if any(row["aircraft_id"] != f"warfare_wings:{airframe}" for row in rows):
            raise ValueError(f"{scenario}: mismatched actual airframe")
        if rows[0]["tick"] != 0 or rows[-1]["tick"] != 400:
            raise ValueError(f"{scenario}: runtime tick horizon incomplete")
    report_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    for airframe in AIRFRAMES:
        scenario = airframe + "-throttle-step-v1"
        source = report_dir / f"{scenario}-reaction-source.csv"
        subprocess.run([java, "-cp", str(classes),
                        "org.kneekura.techhub.warfarewings.physics.ReactionCalibrationTraceMain",
                        str(anchor_csv), f"warfare_wings:{airframe}",
                        str(source)], check=True)
        if not source.is_file():
            raise FileNotFoundError(f"Java17 returned zero but did not write {source}")
        runtime = trace_dir / f"{scenario}-runtime.csv"
        calibrated = compare(source, runtime, report_dir / f"{airframe}-calibration")
        metrics = calibrated["metrics"]
        cases.append({
            "aircraft_id": f"warfare_wings:{airframe}",
            "scenario_id": scenario,
            "runtime_samples": calibrated["samples"],
            "speed_rmse_bps": metrics["speed_error_bps"]["rmse"],
            "speed_final_absolute_error_bps": metrics["speed_error_bps"]["final_abs"],
            "engine_power_rmse": metrics["engine_power_error"]["rmse"],
            "yaw_rmse_deg": metrics["yaw_error_deg"]["rmse"],
            "pitch_rmse_deg": metrics["pitch_error_deg"]["rmse"],
            "position_origin_aligned_final_drift_blocks":
                metrics["position_origin_aligned_drift_blocks"]["final_abs"],
            "status": "CALIBRATION_ONLY_NO_ACCEPTANCE_THRESHOLD",
        })
    report = {
        "schema_version": "ww.physics.representative-exact-jar-calibration.v1",
        "source_anchor_sha256": EXPECTED_SHA256,
        "evidence": "MEASURED_REAL_MINECRAFT_CONTROL_TRACE_VS_SOURCE_V3",
        "conclusion": "FOUR_401_SAMPLE_TRACES_COMPARED_PARITY_NOT_ESTABLISHED",
        "cases": cases,
    }
    (report_dir / "representative-calibrations.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--java", default="java")
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = verify(args.trace_dir, args.anchor, args.java, args.classes, args.output_dir)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"REPRESENTATIVE_EXACT_JAR_CALIBRATION_FAILED: {error}") from None
    for case in report["cases"]:
        print("REAL_MINECRAFT_CALIBRATION", case["aircraft_id"],
              "401 samples", "speed_rmse_bps=", round(case["speed_rmse_bps"], 6),
              "position_origin_aligned_final_drift_blocks=",
              round(case["position_origin_aligned_final_drift_blocks"], 6))
    print(report["conclusion"])


if __name__ == "__main__":
    main()

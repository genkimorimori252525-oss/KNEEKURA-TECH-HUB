#!/usr/bin/env python3
"""Integration tests of the pinned SOURCE batch, Java 17, and standalone report.

Tests run the actual tickWithReaction Java pipeline; no mock physics. Python
verifies independent physical axes, seed reproducibility and report integrity.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from flight_lab_report import load_experiment, make_html
from flight_lab_run import MAIN, MODULE, compile_lab, get_java17, run_lab


class FlightResearchLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javac, cls.java = get_java17()
        cls.temp = tempfile.TemporaryDirectory(prefix="ww-flight-lab-test-")
        cls.root = Path(cls.temp.name)
        cls.classes = cls.root / "classes"
        compile_lab(cls.javac, cls.classes)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def run_small(self, folder: str, seed: int = 345678) -> tuple[dict, Path]:
        output = self.root / folder
        summary = run_lab(self.java, self.classes, output, seed=seed,
                          trials_per_aircraft=22, ticks=100, trace_stride=10)
        make_html(output / "summary.json", output / "time_slices.csv",
                  output / "flight-lab.html")
        return summary, output

    @staticmethod
    def checksum(file: Path) -> str:
        return hashlib.sha256(file.read_bytes()).hexdigest()

    def test_java17_24_aircraft_11_scenarios_and_real_physics(self) -> None:
        summary, output = self.run_small("physics")
        self.assertEqual(summary["aircraft_count"], 24)
        self.assertEqual(summary["scenario_count"], 11)
        self.assertEqual(summary["trial_count"], 528)
        self.assertEqual(summary["simulated_ticks"], 52800)
        self.assertEqual(summary["sampled_traces"], 264)
        self.assertEqual(summary["sampled_time_slice_rows"], 264 * 11)
        self.assertIn("NO_FORGE_PARITY", summary["evidence"])
        self.assertEqual(summary["kernel"], "Ia133Microkernel.tickWithReaction")
        self.assertEqual(summary["wind_baseline"], "PINNED_IA133_SPEED_DEPENDENT_CALM")
        self.assertEqual(summary["wind_stress_overlay"], "SCRIPTED_WIND_ONLY")
        self.assertEqual({g["aircraft_id"] for g in summary["groups"]}.__len__(), 24)
        self.assertEqual(len(summary["groups"]), 24 * 11)
        self.assertEqual(sum(g["trial_count"] for g in summary["groups"]), 528)
        self.assertEqual({g["scenario"] for g in summary["groups"]}, set(summary["scenarios"]))

        def g(aircraft: str, scenario: str) -> dict:
            return next(x for x in summary["groups"]
                        if x["aircraft_id"] == aircraft and x["scenario"] == scenario)

        self.assertEqual(g("warfare_wings:a6m", "CRUISE")["engine_reaction_ticks"], 100)
        self.assertEqual(g("warfare_wings:b17", "CRUISE")["engine_reaction_ticks"], 150)
        self.assertEqual(g("warfare_wings:g10n1", "CRUISE")["engine_reaction_ticks"], 200)
        self.assertGreater(g("warfare_wings:a6m", "TURN_LEFT")["mean_abs_yaw_deg"],
                           g("warfare_wings:a6m", "CRUISE")["mean_abs_yaw_deg"] + 20)
        self.assertGreater(g("warfare_wings:a6m", "CRUISE")["mean_abs_yaw_deg"], 0.05,
                           "pinned calm-weather IA wind should remain active at speed")
        self.assertGreater(g("warfare_wings:a6m", "TURN_RIGHT")["mean_abs_yaw_deg"],
                           g("warfare_wings:a6m", "CRUISE")["mean_abs_yaw_deg"] + 20)
        self.assertGreater(g("warfare_wings:spitfire", "CLIMB")["mean_abs_pitch_deg"],
                           g("warfare_wings:spitfire", "CRUISE")["mean_abs_pitch_deg"] + 10)
        self.assertGreater(g("warfare_wings:a6m", "AI_MISSION_ROUTE")["ai_decision_ticks"], 0)
        self.assertEqual(g("warfare_wings:a6m", "CRUISE")["ai_decision_ticks"], 0)
        self.assertGreater(g("warfare_wings:b17", "AI_FORMATION")["ai_decision_ticks"], 0)
        self.assertEqual(summary["sample_trace_stride_ticks"], 10)
        self.assertTrue((output / "outcomes.csv").is_file())

        with (output / "outcomes.csv").open(newline="", encoding="utf-8") as stream:
            trials = list(csv.DictReader(stream))
        self.assertEqual(len(trials), 528)
        self.assertEqual(len({t["trial_seed"] for t in trials}), len(trials))
        self.assertTrue(all(float(t["path_blocks"]) > 0 for t in trials))
        self.assertTrue(all(int(t["first_90_yaw_tick"]) <= 100 for t in trials))
        self.assertTrue(all(int(t["advisory_fire_ticks"]) == 0 for t in trials))

    def test_same_seed_reproduces_identical_json_csv_and_html(self) -> None:
        _, first = self.run_small("reproduction-a", seed=-123456789)
        _, second = self.run_small("reproduction-b", seed=-123456789)
        for filename in ("summary.json", "outcomes.csv", "time_slices.csv", "flight-lab.html"):
            with self.subTest(filename=filename):
                self.assertEqual(self.checksum(first / filename),
                                 self.checksum(second / filename))
        _, changed = self.run_small("changed-seed", seed=-123456788)
        self.assertNotEqual(self.checksum(first / "outcomes.csv"),
                            self.checksum(changed / "outcomes.csv"))

    def test_offline_report_integrity_and_missing_trace_rejected(self) -> None:
        summary, output = self.run_small("html")
        payload = load_experiment(output / "summary.json", output / "time_slices.csv")
        self.assertEqual(len(payload["traces"]), 24 * 11)
        html = (output / "flight-lab.html").read_text(encoding="utf-8")
        self.assertIn("3D風飛行軌跡", html)
        self.assertIn("NO_FORGE_PARITY", html)
        self.assertIn("canvas id=\"plotTop\"", html)
        self.assertNotIn("<script src=", html.lower())
        self.assertNotIn("<link href=", html.lower())
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

        bad_summary = output / "malformed-summary.json"
        bad = dict(summary)
        bad["sampled_time_slice_rows"] += 1
        bad_summary.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Trace row mismatch"):
            load_experiment(bad_summary, output / "time_slices.csv")

    def test_rejects_incomplete_scenario_matrix(self) -> None:
        result = subprocess.run(
            [self.java, "-cp", str(self.classes), MAIN,
             str(MODULE / "data" / "base-aircraft-anchor-v1.csv"),
             str(self.root / "incomplete"),
             "--trials-per-aircraft", "10", "--ticks", "100"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("minimum 11 trials/aircraft", result.stderr)

    def test_rejects_mismatched_anchor_provenance(self) -> None:
        original = (MODULE / "data" / "base-aircraft-anchor-v1.csv").read_text(encoding="utf-8")
        bad = self.root / "tampered-anchor.csv"
        bad.write_text(original.replace(
            "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43",
            "0" * 64, 1), encoding="utf-8")
        result = subprocess.run(
            [self.java, "-cp", str(self.classes), MAIN,
             str(bad), str(self.root / "bad-provenance"),
             "--trials-per-aircraft", "11", "--ticks", "100"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ANCHOR provenance mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()

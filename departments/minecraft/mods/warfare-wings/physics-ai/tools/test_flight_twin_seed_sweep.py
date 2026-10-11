#!/usr/bin/env python3
"""Adversarial multi-seed SOURCE safety review; original Minecraft NOT_RUN."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from flight_twin_seed_sweep import EXPECTED_SHA, SCHEMA, run, verify_one


class SourceSeedSweepSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="ww-synthetic-24-seed-review-")
        cls.root = Path(cls.temp.name)
        # Genuine Java17 source simulation: 48 different simultaneously
        # physically evolving actor-lifetimes, NOT real Forge GameTests.
        cls.overview = run(cls.root / "two-seeds", None, 20261011, 2, 1, 240)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def case(self, seed: int) -> tuple[dict, Path]:
        directory = self.root / "two-seeds" / f"seed-{seed}"
        data = json.loads((directory / "twin_summary.json").read_text(encoding="utf-8"))
        return data, directory

    def test_two_real_source_24_plane_physical_runs_and_nonparity_labels(self) -> None:
        overview = self.overview
        self.assertEqual(overview["schema"], SCHEMA)
        self.assertIn("NO_FORGE_PARITY", overview["evidence"])
        self.assertEqual(overview["seed_count"], 2)
        self.assertEqual(overview["source_anchor_sha256"], EXPECTED_SHA)
        self.assertEqual(overview["unique_airframes_per_seed"], 24)
        self.assertEqual(overview["total_source_physics_updates"], 24 * 240 * 2)
        self.assertEqual(overview["fixed_safety_gates"], {
            "min_pair_blocks": 6, "b17_protection_blocks": 95})
        self.assertEqual(overview["full_mission_success_seeds"]
                         + overview["failed_mission_seeds"], 2)
        for seed in (20261011, 20261012):
            source, directory = self.case(seed)
            row = verify_one(seed, 240, source, directory)
            self.assertEqual(row["source_physics_updates"], 5760)
            self.assertEqual(row["simultaneous_aircraft"], 24)
            self.assertEqual(row["min_swept_pair_blocks"] < 6,
                             row["swept_pair_breaches_lt6"] > 0)
            self.assertEqual(row["safety_status"] == "FAILED_SOURCE_SAFETY",
                             bool(row["failed_gates"]))
        report = (self.root / "two-seeds" / "seed_sweep.csv")
        self.assertTrue(report.is_file())
        with report.open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))),2)
        offline = self.root / "two-seeds" / "seed_sweep.html"
        self.assertTrue(offline.is_file())
        page = offline.read_text(encoding="utf-8")
        self.assertIn("Independent-Seed SOURCE", page)
        self.assertIn("NOT original Minecraft/Forge", page)
        self.assertIn('seed-20261011/twin_summary.json', page)
        self.assertIn('seed-20261012/twin_summary.json', page)
        self.assertNotIn("<script src=",page)
        self.assertNotIn("<link href=",page)
        self.assertNotIn("https://",page)

    def test_identical_seed_repeated_execution_matches_entire_scientific_csv(self) -> None:
        out = self.root / "repeat"
        run(out, None, 20261011, 1, 1, 240)
        first = self.root / "two-seeds" / "seed-20261011"
        second = out / "seed-20261011"
        for name in ("twin_summary.json", "twin_pairs.csv", "twin_assets.csv",
                     "twin_time_slices.csv", "twin_sensor_events.csv", "twin_units.csv"):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(),
                             f"not byte-identical SOURCE experiment: {name}")

    def test_adversarial_no_false_success_or_threshold_dilution(self) -> None:
        source, directory = self.case(20261011)
        altered = json.loads(json.dumps(source))
        altered["b17_protection_radius_blocks"] = 90
        with self.assertRaisesRegex(ValueError, "6b/95b"):
            verify_one(20261011,240,altered,directory)
        altered = json.loads(json.dumps(source))
        altered["scenarios"][0]["active_aircraft"] = 23
        with self.assertRaisesRegex(ValueError, "24-aircraft"):
            verify_one(20261011,240,altered,directory)
        altered = json.loads(json.dumps(source))
        altered["scenarios"][0]["status"] = "PASS_SOURCE_SAFETY"
        with self.assertRaisesRegex(ValueError, "suppressed"):
            verify_one(20261011,240,altered,directory)
        altered = json.loads(json.dumps(source))
        altered["aircraft_anchor_sha256"] = "not-original"
        with self.assertRaisesRegex(ValueError, "pinned anchor"):
            verify_one(20261011,240,altered,directory)

    def test_corrupted_or_missing_276_pair_receipts_refused(self) -> None:
        original = self.root / "two-seeds" / "seed-20261011"
        target = self.root / "corrupt"
        target.mkdir(exist_ok=True)
        for name in ("twin_pairs.csv","twin_assets.csv"):
            shutil.copy2(original / name,target / name)
        source, _ = self.case(20261011)
        path = target / "twin_pairs.csv"
        with path.open(encoding="utf-8",newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        rows.pop()
        with path.open("w",encoding="utf-8",newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "276 pairs"):
            verify_one(20261011,240,source,target)

    def test_rejects_unsafe_batch_contract_and_seed_integer_overflow(self) -> None:
        for start,count,step,ticks in (
                (20261011,0,1,240), (20261011,2049,1,240),
                (20261011,1,0,240), (20261011,1,1,19),
                ((1 << 63)-1,2,1,240)):
            with self.assertRaises(ValueError):
                run(self.root / f"invalid-{start}-{count}-{step}-{ticks}",
                    None,start,count,step,ticks)


if __name__ == "__main__":
    unittest.main(verbosity=2)

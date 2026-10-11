#!/usr/bin/env python3
"""Deliberately corrupt SOURCE-ONLY fixtures to harden the four-airframe gate.

No fixture is a real Minecraft measurement; successful synthetic tests never
certify aircraft physics or weapon behavior.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from compare_traces import COLUMNS
from verify_representative_calibrations import AIRFRAMES, _validate_atlas, verify

ROOT = Path(__file__).resolve().parent.parent


def fixture(directory: Path, airframe: str, *, samples: int = 401,
            wrong_id: bool = False, frozen: bool = False) -> Path:
    scenario = f"{airframe}-throttle-step-v1"
    path = directory / f"{scenario}-runtime.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for i in range(samples):
            row = {column: "0" for column in COLUMNS}
            row.update(schema_version="ww.physics.trace.v1", source="minecraft_runtime",
                       scenario_id=scenario,
                       aircraft_id="warfare_wings:a6m" if wrong_id else f"warfare_wings:{airframe}",
                       tick=str(i), game_time=str(10000+i),
                       pos_y="200", pos_z=str(min(i, 20) if frozen else i),
                       vel_z="1", speed_bps="20", horizontal_speed_bps="20",
                       engine_target="1", engine_power=str(0.01*(min(i, 20) if frozen else i)))
            writer.writerow(row)
    return path


class RepresentativeCalibrationReceiptTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.anchor = ROOT / "data/base-aircraft-anchor-v1.csv"
        for airframe in AIRFRAMES:
            fixture(self.root, airframe)

    def run_gate(self):
        # The intentionally invalid tests must fail BEFORE launching Java.
        return verify(self.root, self.anchor, "unavailable-java-for-fixture-test",
                      self.root / "nonexistent-classes", self.root / "reports")

    def test_pinned_exact_24_airframe_anchor_is_valid(self):
        _validate_atlas(self.anchor)

    def test_missing_aircraft_does_not_fake_four_successes(self):
        (self.root / "b17-throttle-step-v1-runtime.csv").unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_gate()

    def test_short_aircraft_trace_rejected_before_comparison(self):
        fixture(self.root, "p47n", samples=400)
        with self.assertRaisesRegex(ValueError, "incomplete 401-tick"):
            self.run_gate()

    def test_wrong_aircraft_identity_rejected(self):
        fixture(self.root, "spitfire", wrong_id=True)
        with self.assertRaisesRegex(ValueError, "mismatched actual airframe"):
            self.run_gate()

    def test_frozen_aircraft_despite_clock_advancing_rejected(self):
        fixture(self.root, "il2", frozen=True)
        with self.assertRaisesRegex(ValueError, "NON_TICKING_REAL_AIRCRAFT"):
            self.run_gate()


if __name__ == "__main__":
    unittest.main(verbosity=2)

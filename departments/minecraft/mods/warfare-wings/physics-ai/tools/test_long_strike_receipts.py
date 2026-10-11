#!/usr/bin/env python3
"""Synthetic corrupted-receipt tests for the real two-plane strike gate.

These fabricated CSV fixtures test parser rejection only. They are never
passed off as actual Minecraft flight, damage, landing or mission evidence.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from verify_long_strike_receipts import AIRCRAFT, SAMPLES, verify
from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE, source_airframe_retention


def sample_csv(directory: Path, name: str, *, early_rtb: bool = False,
               clock_gap: bool = False) -> Path:
    identity = AIRCRAFT[name]
    retention = source_airframe_retention()[identity]
    path = directory / f"operational-strike-{name}-forge-controls.csv"
    smooth_x = 0.0
    smooth_z = 0.0
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for tick in range(SAMPLES):
            raw_x = .1 if tick else 0.0
            if tick:
                smooth_x = retention * smooth_x + 0.1 * raw_x
                smooth_z = retention * smooth_z
            phase = "STRIKE_INGRESS" if tick < 190 else (
                "STRIKE_EGRESS" if tick < 311 else "RETURNING")
            if early_rtb and name == "b17" and tick >= 190:
                phase = "RETURNING"
            z = tick * .65 if tick < 190 else (
                123.5 + (tick - 190) * .1 if tick < 311 else
                135.6 - (tick - 311) * .65)
            row = {field: "0" for field in COLUMNS}
            row.update(schema_version=SCHEMA, source=SOURCE,
                       scenario_id=f"operational-strike-{name}", aircraft_id=identity,
                       sim_tick=str(tick), game_time=str(10000+tick+(1 if clock_gap and tick>300 else 0)),
                       pos_x=str(-100 if name == "il2" else 100), pos_y="200",
                       pos_z=f"{z:.9f}", vel_z="0.65", yaw_deg=f"{tick*.02:.9f}",
                       engine_target=".8", engine_power=".5",
                       smooth_x=f"{smooth_x:.12f}", smooth_z=f"{smooth_z:.12f}",
                       command_x=str(raw_x), command_throttle=".8",
                       maneuver="INITIAL" if not tick else "PATROL_ROUTE",
                       reason="INITIAL" if not tick else f"geometry_fixture|phase={phase}|phase_reason=fixture",
                       world_safety_reason="INITIAL" if not tick else "CLEAR",
                       terrain_clearance_blocks="150")
            writer.writerow(row)
    return path


class LongStrikeReceiptTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        for name in AIRCRAFT:
            sample_csv(self.root, name)

    def test_well_formed_synthetic_fixture_passes_parser_only(self):
        outcome = verify(self.root)
        self.assertEqual(outcome["conclusion"], "NO_WEAPON_GEOMETRIC_APPROACH_EGRESS_RTB_PASSED")
        self.assertEqual(len(outcome["units"]), 2)

    def test_missing_actual_actor_is_not_inferred(self):
        (self.root / "operational-strike-b17-forge-controls.csv").unlink()
        with self.assertRaises((FileNotFoundError, ValueError)):
            verify(self.root)

    def test_early_return_cannot_fake_completed_egress(self):
        sample_csv(self.root, "b17", early_rtb=True)
        report = verify(self.root)
        self.assertTrue(any(v.startswith("PHASES_INCOMPLETE_OR_OUT_OF_ORDER:b17")
                            or v.startswith("PHASE_DURATION_FAILED:b17")
                            for v in report["failed_operational_gates"]))

    def test_skipped_real_server_clock_rejected(self):
        sample_csv(self.root, "il2", clock_gap=True)
        with self.assertRaisesRegex(ValueError, "nonconsecutive game tick"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)

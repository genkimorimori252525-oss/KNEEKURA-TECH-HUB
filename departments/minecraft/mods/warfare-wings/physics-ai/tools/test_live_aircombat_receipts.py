#!/usr/bin/env python3
"""Synthetic tamper fixtures for the independent REAL multi-aircraft receipt gate.

Fixtures prove rejection mechanics, not actual Minecraft operational success.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from verify_live_aircombat_receipts import OperationalFailure, verify
from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE

TICKS = 140


def make_flight(root: Path, ident: str, team: str, x: float, z: float,
                *, glitch: str = "") -> dict:
    flight = {"id": ident, "file": f"{ident}.csv", "scenario_id": ident,
              "aircraft_id": "warfare_wings:a6m" if team == "red" else "warfare_wings:p47n",
              "team": team}
    with (root / flight["file"]).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for tick in range(TICKS + 1):
            row = {key: "0" for key in COLUMNS}
            row.update(schema_version=SCHEMA, source=SOURCE, scenario_id=ident,
                       aircraft_id=flight["aircraft_id"], sim_tick=str(tick),
                       game_time=str(10000 + tick), pos_x=str(x), pos_y="170",
                       pos_z=str(z + (min(tick, 50) if glitch == "frozen-physics" else tick) * 0.8),
                       vel_z="0.8", maneuver="PATROL",
                       reason="actual_control", world_safety_reason="CLEAR")
            if glitch == "unsynced" and tick >= 50:
                row["game_time"] = str(10001 + tick)
            elif glitch == "forged-source":
                row["source"] = "scripted_source_simulation"
            elif glitch == "nan" and tick == 50:
                row["pos_x"] = "NaN"
            writer.writerow(row)
    return flight


class MultiAircraftReceiptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.flights = [
            make_flight(self.root, "asset", "blue", 0, 0),
            make_flight(self.root, "escort", "blue", 45, 0),
            make_flight(self.root, "enemy", "red", 0, 200),
            make_flight(self.root, "enemy2", "red", 100, 200),
        ]
        self.manifest = {"kind": "escort", "source": SOURCE, "scenario": "sample",
                         "ticks": TICKS, "flights": self.flights, "assets": ["asset"],
                         "escort_assignments": {"asset": ["escort"]}}

    def test_healthy_geometry_no_kill_claim(self):
        report = verify(self.manifest, self.root)
        self.assertEqual(report["observed_aircraft"], 4)
        self.assertEqual(len(report["pairs"]), 6)
        self.assertEqual(report["protected_assets"][0]["hostile_inside_95_blocks_ticks"], 0)
        self.assertEqual(report["conclusion"], "GEOMETRIC_GATES_PASSED_NO_WEAPON_OR_KILL_PROOF")

    def test_close_intruder_is_not_silently_accepted(self):
        self.flights[-2] = make_flight(self.root, "enemy", "red", 0, 80)
        report = verify(self.manifest, self.root)
        self.assertIn("ESCORT_PROTECTION_BREACHED:asset:ticks=141", report["failed_operational_gates"])
        self.assertEqual(report["conclusion"], "FAILED")

    def test_body_collision_is_failure(self):
        self.flights[-2] = make_flight(self.root, "enemy", "red", 3, 0)
        report = verify(self.manifest, self.root)
        self.assertTrue(any(x.startswith("BODY_SEPARATION_LT6:asset:enemy:") for x in report["failed_operational_gates"]))

    def test_unsynchronized_flights_rejected(self):
        self.flights[-1] = make_flight(self.root, "enemy2", "red", 100, 200, glitch="unsynced")
        with self.assertRaisesRegex(OperationalFailure, "frozen or skipped game tick"):
            verify(self.manifest, self.root)

    def test_forged_source_rejected(self):
        self.flights[-1] = make_flight(self.root, "enemy2", "red", 100, 200, glitch="forged-source")
        with self.assertRaisesRegex(OperationalFailure, "runtime identity"):
            verify(self.manifest, self.root)

    def test_nonfinite_position_rejected(self):
        self.flights[-1] = make_flight(self.root, "enemy2", "red", 100, 200, glitch="nan")
        with self.assertRaisesRegex(OperationalFailure, "nonfinite pos_x"):
            verify(self.manifest, self.root)

    def test_frozen_physics_while_server_ticks_rejected(self):
        self.flights[-1] = make_flight(self.root, "enemy2", "red", 100, 200, glitch="frozen-physics")
        with self.assertRaisesRegex(OperationalFailure, "non-moving aircraft physics snapshot"):
            verify(self.manifest, self.root)

    def test_duplicate_aircraft_receipt_rejected(self):
        self.manifest["flights"].append(dict(self.flights[0], id="duplicate"))
        with self.assertRaisesRegex(OperationalFailure, "Duplicate flight IDs or receipts"):
            verify(self.manifest, self.root)

    def test_missing_receipt_does_not_pass(self):
        self.flights[-1]["file"] = "unobserved-aircraft.csv"
        with self.assertRaisesRegex(OperationalFailure, "Missing real runtime trace"):
            verify(self.manifest, self.root)

    def test_escaping_directory_rejected(self):
        self.flights[-1]["file"] = "../outside.csv"
        with self.assertRaisesRegex(OperationalFailure, "beneath"):
            verify(self.manifest, self.root)

    def test_no_assigned_escort_rejected(self):
        self.manifest["flights"] = [self.flights[0], self.flights[2]]
        with self.assertRaisesRegex(OperationalFailure, "both actual escort and hostile"):
            verify(self.manifest, self.root)

    def test_unassigned_friendly_does_not_count_as_escort(self):
        self.manifest["escort_assignments"] = {"asset": ["enemy"]}
        with self.assertRaisesRegex(OperationalFailure, "both actual escort and hostile"):
            verify(self.manifest, self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)

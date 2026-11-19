#!/usr/bin/env python3
"""Synthetic hostile-receipt adversarial fixtures: never real Forge evidence."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from verify_live_threat_receipts import CASES, SAMPLES, verify
from verify_tactical_runtime_receipts import COLUMNS, SCHEMA, SOURCE


class ObservedThreatReceiptFixtures(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="ww-synthetic-observed-risk-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.make()

    def make(self, scenario_edit: str = "", bad_tick: int = -1,
             field: str | None = None, value: str = "", drop_last: bool = False) -> None:
        for scenario, airplane in CASES.items():
            with (self.root / f"{scenario}-forge-controls.csv").open(
                    "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                for tick in range(SAMPLES - (1 if scenario == scenario_edit and drop_last else 0)):
                    row = dict.fromkeys(COLUMNS, "0")
                    row.update(schema_version=SCHEMA, source=SOURCE, scenario_id=scenario,
                               aircraft_id=airplane,
                               sim_tick=str(tick), game_time=str(30000 + tick),
                               pos_y="220", pos_z=str(tick), vel_z="1",
                               maneuver="INITIAL" if tick == 0 else "ESCORT_SCREEN",
                               reason="INITIAL" if tick == 0 else (
                                   "ESCORT_PREDICTIVE_SCREEN|live_team=convoy"
                                   "|sighting=visible:12345678-1234-1234-1234-123456789abc"
                                   "|visible_hostile_count=2"
                                   "|contact_selection=VISIBLE_CPA_TO_PROTECTED_ASSET"
                                   "|phase=ESCORT_COVER"),
                               world_safety_reason="CLEAR",
                               terrain_clearance_blocks="100")
                    if scenario == scenario_edit and tick == bad_tick and field:
                        row[field] = value
                    writer.writerow(row)

    def test_complete_synthetic_fixture_parses_only(self) -> None:
        report = verify(self.root)
        self.assertEqual(len(report["cases"]), 3)
        self.assertIn("MULTI_CONTACT_SELECTION", report["conclusion"])
        self.assertEqual(report["b17_95_block_protection"], "NOT_ASSESSED_HERE")
        self.assertTrue(all(x["two_visible_opponents_ticks"] == 340 for x in report["cases"]))

    def test_missing_real_actor_fails_closed(self) -> None:
        (self.root / "op-b17-forge-controls.csv").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Missing original-Forge"):
            verify(self.root)

    def test_missing_340th_tick_fails_closed(self) -> None:
        self.make("op-escort-right", drop_last=True)
        with self.assertRaisesRegex(ValueError, "341 actual entity states"):
            verify(self.root)

    def test_missing_game_time_fails_closed(self) -> None:
        self.make("op-escort-left", 270, "game_time", "30275")
        with self.assertRaisesRegex(ValueError, "missing real server tick"):
            verify(self.root)

    def test_nonzero_visible_hostile_requires_real_selection(self) -> None:
        self.make("op-b17", 20, "reason",
                  "FAKE|live_team=convoy|sighting=none|visible_hostile_count=2"
                  "|contact_selection=NO_VISIBLE_HOSTILE|phase=ESCORT_COVER")
        with self.assertRaisesRegex(ValueError, "no safe observed-threat selection"):
            verify(self.root)

    def test_observed_selection_cannot_rank_hidden_contact(self) -> None:
        self.make("op-escort-left", 15, "reason",
                  "FAKE|live_team=convoy|sighting=none|visible_hostile_count=0"
                  "|contact_selection=VISIBLE_CPA_TO_PROTECTED_ASSET|phase=ESCORT_COVER")
        with self.assertRaisesRegex(ValueError, "invisible or unsupported"):
            verify(self.root)

    def test_nonhostile_team_is_rejected(self) -> None:
        self.make("op-b17", 10, "reason",
                  "FAKE|live_team=raiders|sighting=visible:12345678-1234-1234-1234-123456789abc"
                  "|visible_hostile_count=1|contact_selection=VISIBLE_CPA_TO_PROTECTED_ASSET"
                  "|phase=TRANSIT")
        with self.assertRaisesRegex(ValueError, "explicit allied team"):
            verify(self.root)

    def test_unbounded_enemy_knowledge_is_rejected(self) -> None:
        self.make("op-b17", 10, "reason",
                  "FAKE|live_team=convoy|sighting=visible:12345678-1234-1234-1234-123456789abc"
                  "|visible_hostile_count=999|contact_selection=VISIBLE_CPA_TO_PROTECTED_ASSET"
                  "|phase=TRANSIT")
        with self.assertRaisesRegex(ValueError, "unverified visible-hostile count"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)

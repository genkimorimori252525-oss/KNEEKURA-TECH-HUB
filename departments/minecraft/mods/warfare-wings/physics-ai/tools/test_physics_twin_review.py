#!/usr/bin/env python3
"""Entirely synthetic, non-Forge fixtures proving twin review fails closed.

Fixtures imitate column names to test rejection only. No model metrics
returned by this test establish the real Minecraft physical accuracy.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from physics_twin_review import NEUTRAL_SCHEMA, analyze_one, verify

BASE = {
    "scenario_id": "a6m-throttle-step-v1", "aircraft_id": "warfare_wings:a6m",
    "trace_kind": "neutral_pinned_wind",
    "assumptions": "AIRBORNE_PINNED_IA_WIND|ENGINE_POWER_OBSERVED|ROLL_OBSERVED",
    "one_step_pos_error_blocks": ".000001",
    "one_step_vel_error_bpt": ".000001",
    "one_step_yaw_error_deg": ".00000001",
    "one_step_pitch_error_deg": ".00000001",
    "one_step_roll_error_deg": "0",
    "one_step_engine_power_error": ".00000001",
    "one_step_smooth_x_error": "0",
    "one_step_smooth_z_error": "0",
    "free_run_pos_error_blocks": ".0002",
    "free_run_vel_error_bpt": ".000001",
    "free_run_speed_error_bps": ".00001",
    "free_run_yaw_error_deg": ".00001",
    "free_run_pitch_error_deg": ".00001",
}


def fixture(root: Path, *, fake_drift: float = .0002,
            fake_game_clock: bool = False) -> None:
    root.joinpath("real").mkdir(exist_ok=True)
    root.joinpath("twins").mkdir(exist_ok=True)
    real_path = root / "real/a6m-throttle-step-v1-runtime.csv"
    with real_path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=NEUTRAL_SCHEMA.split(","))
        writer.writeheader()
        for i in range(4):
            row={col:"0" for col in writer.fieldnames}
            row.update(schema_version="ww.physics.trace.v1",source="minecraft_runtime",
                       scenario_id=BASE["scenario_id"],aircraft_id=BASE["aircraft_id"],
                       tick=str(i),game_time=str(100+i),pos_x="0",pos_y="200",
                       pos_z=f"{i*.7:.9f}",vel_z=".7",speed_bps="14",
                       horizontal_speed_bps="14",engine_target="1",fuel_utilization="1")
            writer.writerow(row)
    replay_path = root / "twins/a6m-pinned-wind.csv"
    fields=["scenario_id","aircraft_id","tick","game_time","real_pos_x","real_pos_y","real_pos_z",
            "real_vel_x","real_vel_y","real_vel_z",*[
                column for column in BASE if column not in ("scenario_id","aircraft_id")]]
    with replay_path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        for i in range(1,4):
            row={**BASE,"tick":str(i),"game_time":str(100+i+(1 if fake_game_clock and i==2 else 0)),
                 "real_pos_x":"0","real_pos_y":"200","real_pos_z":f"{i*.7:.9f}",
                 "real_vel_x":"0","real_vel_y":"0","real_vel_z":".7",
                 "free_run_pos_error_blocks":str(fake_drift)}
            writer.writerow(row)


class TwinOriginalGameTestReceiptFixtures(unittest.TestCase):
    def setUp(self):
        self.scratch=tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root=Path(self.scratch.name)
        fixture(self.root)

    def one(self):
        return analyze_one(self.root/"twins/a6m-pinned-wind.csv",self.root/"real")

    def test_valid_parser_fixture_not_actual_flight_proof(self):
        result,series=self.one()
        self.assertEqual(result["ticks"],3)
        self.assertEqual(len(series),3)
        report=verify(self.root/"twins",self.root/"real",self.root/"html",expected_neutral=1,max_final_drift=.01)
        self.assertEqual(report["failed_gates"],[])
        output=(self.root/"html/physics-twin-explorer.html").read_text(encoding="utf-8")
        self.assertIn("Selected error over actual Minecraft ticks",output)
        self.assertNotIn("https://",output)
        self.assertEqual(report["cases"],1)

    def test_source_csv_is_not_accepted_as_original_forge(self):
        path=self.root/"real/a6m-throttle-step-v1-runtime.csv"
        path.write_text(path.read_text().replace("minecraft_runtime","microkernel"),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"not an unchanged real Minecraft"):
            self.one()

    def test_replay_cannot_replace_original_measured_position(self):
        path=self.root/"twins/a6m-pinned-wind.csv"
        text=path.read_text(encoding="utf-8").replace("1.400000000","1.499000000")
        path.write_text(text,encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"state substituted"):
            self.one()

    def test_missing_original_recording_cannot_infer_parity(self):
        (self.root/"real/a6m-throttle-step-v1-runtime.csv").unlink()
        with self.assertRaises(FileNotFoundError):
            self.one()

    def test_missing_24_forge_replays_is_not_silently_waived(self):
        with self.assertRaisesRegex(ValueError,"coverage incomplete"):
            verify(self.root/"twins",self.root/"real",None,expected_roster=24)

    def test_real_clock_and_offline_tick_must_match(self):
        fixture(self.root,fake_game_clock=True)
        with self.assertRaisesRegex(ValueError,"non-matching offline physical replay"):
            self.one()

    def test_physical_accuracy_gate_reports_failure_when_not_met(self):
        fixture(self.root,fake_drift=.25)
        report=verify(self.root/"twins",self.root/"real",None,max_final_drift=.01)
        self.assertEqual(report["conclusion"],"RECORDED_FREE_AIR_PHYSICS_GATE_FAILED")
        self.assertEqual(len(report["failed_gates"]),1)

    def test_unknown_wind_mode_is_rejected(self):
        path=self.root/"twins/a6m-pinned-wind.csv"
        path.write_text(path.read_text(encoding="utf-8").replace("neutral_pinned_wind","legacy_zero_wind"),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"omitted exact IA wind model"):
            self.one()

    def test_nonfinite_physics_is_rejected(self):
        path=self.root/"twins/a6m-pinned-wind.csv"
        path.write_text(path.read_text(encoding="utf-8").replace(".000001","NaN"),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            self.one()


if __name__ == "__main__":
    unittest.main(verbosity=2)

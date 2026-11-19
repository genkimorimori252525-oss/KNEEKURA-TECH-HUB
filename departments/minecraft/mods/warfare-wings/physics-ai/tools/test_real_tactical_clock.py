#!/usr/bin/env python3
"""Source-only adversarial fixtures for the original-Forge replay clock contract.

The generated input resembles the receipt schema but is NOT Minecraft evidence.
These tests only establish that the replay refuses missing game/entity ticks;
they cannot prove parity, combat, real 840-tick flight or successful protection.
"""

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import tempfile
import unittest

from flight_lab_run import get_java17
from run_physics_twin import SOURCE_FILES
from verify_tactical_runtime_receipts import COLUMNS


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "org.kneekura.techhub.warfarewings.physics"


class TacticalOriginalClockRejectsCorruption(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scratch = tempfile.TemporaryDirectory(prefix="ww-source-clock-test-")
        cls.classes = Path(cls.scratch.name) / "classes"
        cls.classes.mkdir()
        cls.javac, cls.java = get_java17()
        source = ROOT / "src/main/java" / Path(PACKAGE.replace(".", "/"))
        subprocess.run([str(cls.javac), "-encoding", "UTF-8", "--release", "17",
                        "-d", str(cls.classes),
                        *(str(source / name) for name in SOURCE_FILES)],
                       check=True, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scratch.cleanup()

    def _fixture(self, *, skipped_server_ticks: int = 0,
                 wrong_aircraft_tick: bool = False,
                 wrong_source: bool = False) -> Path:
        path = Path(self.scratch.name) / "adversarial-source-fixture.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for tick in range(5):
                row = dict.fromkeys(COLUMNS, "0")
                row.update(
                    schema_version="ww.physics.forge-tactical-pilot.v1",
                    source=("source_only_fake" if wrong_source
                            else "minecraft_runtime_ia_next_tick_injection"),
                    scenario_id="adversarial-clock",
                    aircraft_id="warfare_wings:b17",
                    sim_tick=str(tick + (1 if wrong_aircraft_tick and tick == 4 else 0)),
                    game_time=str(100 + tick + (skipped_server_ticks if tick == 4 else 0)),
                    pos_x="0", pos_y="200", pos_z=str(tick),
                    vel_x="0", vel_y="0", vel_z="1",
                    yaw_deg="0", pitch_deg="0", engine_target="1",
                    engine_power=str(tick / 150),
                    smooth_x="0", smooth_z="0", command_x="0",
                    command_z="0", command_throttle="1",
                    maneuver="INITIAL" if tick == 0 else "PATROL_ROUTE",
                    reason="INITIAL" if tick == 0 else "SOURCE_ONLY_FIXTURE",
                    world_safety_reason="INITIAL" if tick == 0 else "CLEAR",
                    terrain_clearance_blocks="100")
                writer.writerow(row)
        return path

    def _replay(self, source: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([str(self.java), "-cp", str(self.classes),
                               PACKAGE + ".RealTacticalPhysicsTwinReplayMain",
                               str(ROOT / "data/base-aircraft-anchor-v1.csv"),
                               "warfare_wings:b17", "adversarial-clock",
                               str(source), str(Path(self.scratch.name) / "output.csv"),
                               "--pinned-wind"],
                              capture_output=True, text=True, errors="replace")

    def test_skipped_original_server_ticks_fail_closed(self) -> None:
        # 103 -> 117 is a 13-tick loss, even if consecutive aircraft tick
        # counters could be spoofed by an incomplete generated receipt.
        result = self._replay(self._fixture(skipped_server_ticks=13))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ORIGINAL_MINECRAFT_SERVER_CLOCK_GAP", result.stderr)
        self.assertIn("missing_server_ticks=13", result.stderr)
        self.assertFalse((Path(self.scratch.name) / "output.csv").exists())

    def test_skipped_original_aircraft_tick_fails_closed(self) -> None:
        result = self._replay(self._fixture(wrong_aircraft_tick=True))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Non-consecutive ORIGINAL aircraft physics tick", result.stderr)

    def test_fabricated_source_is_not_accepted_as_real_receipt(self) -> None:
        result = self._replay(self._fixture(wrong_source=True))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Real tactical physics identity/source changed", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

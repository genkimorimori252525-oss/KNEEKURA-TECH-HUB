#!/usr/bin/env python3
"""Original Forge triple-run timeline checks; explicit SKIP without owner data."""

from __future__ import annotations

import unittest

from forensic_b17_three_run import DEFAULT_ROOTS, analyze
from forensic_b17_compare import ForensicEvidenceError


class ThreeOriginalForgePolicySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not all(path.is_dir() for path in DEFAULT_ROOTS):
            raise unittest.SkipTest(
                "Private owner-original 49/105/81 Forge CSVs unavailable; "
                "never substitute synthetic SOURCE tracks")
        cls.summary,cls.rows=analyze(DEFAULT_ROOTS,quarantine=True)

    def test_independent_recomputed_real_contiguous_340tick_evidence(self) -> None:
        self.assertEqual(len(self.rows),341)
        self.assertEqual([r["tick"] for r in self.rows],list(range(341)))
        self.assertEqual(self.summary["actor_count_per_original_game_test"],5)
        self.assertEqual(self.summary["synchronized_actor_physics_ticks"],340)
        self.assertEqual(self.summary["min_pair_separation_gate_blocks"],6)
        self.assertEqual(self.summary["b17_zero_intrusion_gate_blocks"],95)
        self.assertIn("ORIGINAL_REAL_MINECRAFT",self.summary["evidence"])
        for record in self.summary["runs"]:
            self.assertEqual(record["real_source"],
                             "minecraft_runtime_ia_next_tick_injection")
            self.assertEqual(len(record["original_hashes"]),8,
                             "Expected independently hashed complete original Forge root inputs")
            self.assertIn(record["native_operational_verdict"],(
                "FAILED", "GEOMETRIC_GATES_PASSED_NO_WEAPON_OR_KILL_PROOF"))
            self.assertGreaterEqual(record["strict_340_actor_physics_intrusion_ticks"],0)
            self.assertLessEqual(record["strict_340_actor_physics_intrusion_ticks"],340)
            if record["strict_340_actor_physics_intrusion_ticks"] > 0:
                self.assertEqual(record["native_operational_verdict"],"FAILED",
                                 "Real B17 95b breach must never be reported as a win")

    def test_three_original_policy_timelines_and_input_divergence(self) -> None:
        self.assertEqual([x["policy_label"] for x in self.summary["runs"]],
                         ["nearest","protected_asset_cpa","protected_asset_cpa_retained"])
        self.assertEqual([x["strict_340_actor_physics_intrusion_ticks"]
                          for x in self.summary["runs"][:2]], [49,104])
        # Third root is the current owner GameTest folder and is refreshed
        # by legitimate future policy work. Never freeze its earlier 81tick
        # FAILED result as a test oracle that would reject a genuine win.
        self.assertIn(self.summary["runs"][2]["strict_340_actor_physics_intrusion_ticks"],
                      range(341))
        first=self.summary["nearest_to_cpa_first_changed_control_by_actor"]
        second=self.summary["cpa_to_retained_first_changed_control_by_actor"]
        self.assertEqual(first["escort-right"],1)
        self.assertEqual(first["b17"],47)
        self.assertEqual(second["b17"],47)
        self.assertNotEqual(self.rows[1]["nearest_escort-right_raw_x"],
                            self.rows[1]["protected_asset_cpa_escort-right_raw_x"])

    def test_corrupt_or_missing_original_third_run_fails_closed(self) -> None:
        roots=(DEFAULT_ROOTS[0],DEFAULT_ROOTS[1],DEFAULT_ROOTS[0])
        with self.assertRaisesRegex(ForensicEvidenceError,"unique"):
            analyze(roots,quarantine=True)
        roots=(DEFAULT_ROOTS[0],DEFAULT_ROOTS[1],DEFAULT_ROOTS[0]/"absent")
        with self.assertRaises(ForensicEvidenceError):
            analyze(roots,quarantine=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

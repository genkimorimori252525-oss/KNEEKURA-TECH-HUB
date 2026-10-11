#!/usr/bin/env python3
"""Optional two-REAL Forge B17 policy change comparison with quarantined old sidecars.

No synthetic REAL fixture: owner-private ignored receipts, if absent, skip.
Safety conditions are verified against independently recomputed each-run
geometry; no frozen particular policy failure status is required.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from forensic_b17_compare import DEFAULT_MANIFEST, load_verified_real
from forensic_b17_policy_delta import (
    DEFAULT_BEFORE,DEFAULT_AFTER,UNITS,SCHEMA,compare_real_runs,save_policy_delta,
)


class RealForgePolicyDeteriorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEFAULT_BEFORE.is_dir() or not DEFAULT_AFTER.is_dir():
            raise unittest.SkipTest("Original before/after ignored REAL Forge roots unavailable")
        cls.before=load_verified_real(
            DEFAULT_BEFORE,quarantine_stale_sidecar=True)
        cls.after=load_verified_real(
            DEFAULT_AFTER,quarantine_stale_sidecar=True)
        cls.summary,cls.frames,cls.actors=compare_real_runs(cls.before,cls.after)
        cls.temp=tempfile.TemporaryDirectory(prefix="ww-real-b17-policy-audit-")
        cls.out=Path(cls.temp.name)
        save_policy_delta(cls.out,cls.summary,cls.frames,cls.actors)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_both_independent_authentic_clocks_and_schemas(self):
        self.assertEqual(self.summary["schema"],SCHEMA)
        self.assertEqual(self.summary["ticks"],340)
        self.assertEqual(self.summary["unit_count"],5)
        self.assertEqual(len(self.frames),341)
        self.assertEqual(len(self.actors),341*5)
        for run in (self.before,self.after):
            self.assertEqual(run.saved_sidecar_status,
                             "STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED")
            self.assertEqual(run.sidecar["source"],
                             "minecraft_runtime_ia_next_tick_injection")
            self.assertEqual(len(run.traces["b17"]),341)
            self.assertEqual(len(run.geometry),341)
            for i in range(341):
                self.assertEqual({run.traces[u][i]["game_time"] for u in UNITS},
                                 {run.game_time_zero+i})

    def test_before_after_strict_safety_never_diluted(self):
        self.assertEqual(self.summary["physical_distance_limit_blocks"],6)
        self.assertEqual(self.summary["b17_protection_limit_blocks"],95)
        for marker,run in (("before",self.before),("after",self.after)):
            report=self.summary[marker]
            self.assertEqual(report["real_acceptance_recomputed"],
                             run.sidecar["conclusion"])
            self.assertEqual(report["strict_inside95_ticks"],
                             run.sidecar["protected_assets"][0][
                                 "hostile_inside_95_blocks_ticks"])
            self.assertEqual(report["body_lt6_pair_ticks"],
                             sum(pair["under_6_blocks_ticks"] for pair in run.sidecar["pairs"]))
            self.assertEqual(report["original_saved_sidecar_status"],
                             "STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED")
            self.assertEqual(len(report["sha256_by_original_real_filename"]),8)
        self.assertEqual(
            self.summary["change"]["after_minus_before_inside95_ticks"],
            self.summary["after"]["strict_inside95_ticks"]-
            self.summary["before"]["strict_inside95_ticks"])

    def test_source_never_laundered_as_real_and_per_actor_explanations(self):
        self.assertIn("TWO_SEPARATELY_VERIFIED_ACTUAL_MINECRAFT",
                      self.summary["evidence"])
        self.assertEqual({u["unit_id"] for u in self.summary["per_unit"]},set(UNITS))
        self.assertTrue(all(record["schema"]==SCHEMA and
                            "REAL tick" in record["unit_tick_explanation"]
                            for record in self.actors))
        self.assertTrue(all(record["real_tick_explanation"].startswith("At REAL")
                            for record in self.frames))
        self.assertTrue(all(record["before_maneuver"] and record["after_maneuver"]
                            for record in self.actors))
        self.assertGreater(sum(u["ticks_with_distinct_raw_input"]
                               for u in self.summary["per_unit"]),0)

    def test_report_deterministic_given_unchanged_original_real_bytes(self):
        # Input hashes are recomputed, because latest owner REAL roots may be
        # regenerated during development. A changed upstream receipt is a
        # distinct dataset and must never be compared as the same frozen run.
        for label,run in (("before",self.before),("after",self.after)):
            for filename,recorded in run.sha256.items():
                path=(DEFAULT_MANIFEST if filename==DEFAULT_MANIFEST.name
                      else run.root/filename)
                if not path.exists():
                    raise AssertionError("Lost original REAL receipt "+filename)
                current=hashlib.sha256(path.read_bytes()).hexdigest()
                if current!=recorded:
                    self.skipTest(f"Owner REAL {label} changed since verified read")
        nextdir=self.out/"duplicate"
        save_policy_delta(nextdir,self.summary,self.frames,self.actors)
        for filename in ("forensic_b17_real_policy_delta.json",
                         "forensic_b17_real_policy_ticks.csv",
                         "forensic_b17_real_policy_units.csv",
                         "forensic_b17_real_policy_findings.md"):
            a=hashlib.sha256((self.out/filename).read_bytes()).hexdigest()
            b=hashlib.sha256((nextdir/filename).read_bytes()).hexdigest()
            self.assertEqual(a,b)


if __name__=="__main__":
    unittest.main()

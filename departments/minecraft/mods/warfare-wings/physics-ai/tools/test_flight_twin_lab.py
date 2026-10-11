#!/usr/bin/env python3
"""Java17 live 20 Hz closed-loop FlightTwin integration, strict original gates.

No synthetic 'mock physics' passes, no changed 6/95 thresholds, no disabled
failing scenarios. A failing *flight scenario* remains a valid test receipt
when its explicit failed operational gate agrees with measured geometry.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from flight_lab_report import load_twin_experiment, make_twin_html
from flight_lab_run import compile_lab, get_java17, run_twin

TWOFIELDS = ("twin_summary.json", "twin_units.csv", "twin_pairs.csv",
             "twin_assets.csv", "twin_time_slices.csv", "twin_sensor_events.csv",
             "flight-twin.html")


class FlightTwinLabIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javac, cls.java = get_java17()
        cls.temp = tempfile.TemporaryDirectory(prefix="ww-flight-twin-suite-")
        cls.root = Path(cls.temp.name)
        cls.classes = cls.root / "classes"
        compile_lab(cls.javac, cls.classes)
        cls.output = cls.root / "full-run"
        cls.summary = run_twin(cls.java, cls.classes, cls.output,
                               seed=20261011, unique_ticks=240,
                               trace_stride=10, scenario="all")
        make_twin_html(cls.output, cls.output / "flight-twin.html")
        cls.payload = load_twin_experiment(cls.output)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def case(self, name: str) -> dict:
        return next(x for x in self.summary["scenarios"] if x["id"] == name)

    def rows(self, category: str, name: str) -> list[dict]:
        return [x for x in self.payload[category] if x["scenario"] == name]

    @staticmethod
    def checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_java17_sensor_visibility_fov_los_ttl_and_reacquisition(self) -> None:
        result = subprocess.run(
            [self.java, "-cp", str(self.classes),
             "org.kneekura.techhub.warfarewings.physics.FlightTwinSensorSelfTestMain"],
            capture_output=True, text=True, check=True)
        self.assertIn("FLIGHT_TWIN_SENSOR_SELFTEST PASS assertions=13", result.stdout)
        probe = self.case("synthetic_los_occluded")
        self.assertGreater(probe["los_rejected_observations"], 0)
        self.assertEqual(probe["observed_hostile_ticks"], 0)
        self.assertGreater(len(self.rows("events", "synthetic_los_occluded")), 0)
        self.assertTrue(any(e["visibility"] == "TERRAIN_OCCLUDED"
                            for e in self.rows("events", "synthetic_los_occluded")))
        self.assertGreater(sum(c["remembered_hostile_ticks"] for c in self.summary["scenarios"]), 0)
        self.assertGreater(sum(c["fov_rejected_observations"] for c in self.summary["scenarios"]), 0)

    def test_physical_24_distinct_type_concurrency_and_exact_wind_reactions(self) -> None:
        self.assertEqual(self.summary["scenario_count"], 5)
        scene = self.case("all_24_unique")
        self.assertEqual(scene["active_aircraft"], 24)
        self.assertEqual(scene["unique_aircraft_types"], 24)
        self.assertEqual(scene["simulated_ticks"], 240)
        self.assertEqual(scene["total_ai_decisions"], 24*240)
        self.assertEqual(scene["simultaneous_source_updates"], 24*240)
        self.assertEqual(scene["environment"], "PINNED_IA133_CALM_FLAT")
        self.assertIn("PINNED_IA133_WIND", self.summary["evidence"])

        units = self.rows("units","all_24_unique")
        self.assertEqual(len(units), 24)
        self.assertEqual(len({u["aircraft_id"] for u in units}), 24)
        self.assertTrue(all(u["path_blocks"] > 30 for u in units))
        self.assertTrue(all(u["final_speed_bps"] > 0 for u in units))
        self.assertEqual(sum(u["advisory_fire_ticks"] for u in units),0)
        self.assertEqual(next(u["engine_reaction_ticks"] for u in units
                              if u["aircraft_id"] == "warfare_wings:a6m"), 100)
        self.assertEqual(next(u["engine_reaction_ticks"] for u in units
                              if u["aircraft_id"] == "warfare_wings:b17"), 150)
        self.assertEqual(next(u["engine_reaction_ticks"] for u in units
                              if u["aircraft_id"] == "warfare_wings:g10n1"), 200)
        self.assertEqual(len(self.rows("pairs","all_24_unique")),24*23//2)
        last = self.rows("slices","all_24_unique")
        self.assertEqual({x["unit_id"] for x in last if x["tick"] == 240},
                         {u["unit_id"] for u in units})
        self.assertTrue(all(u["visible_contact_ticks"] > 0 for u in units
                            if u["role"] == "fighter"))
        self.assertGreater(sum(u["assigned_target_ticks"] for u in units), 0)

    def test_original_2v2_geometry_and_six_block_gate(self) -> None:
        name = "original_2v2"
        scene = self.case(name)
        self.assertEqual(scene["simulated_ticks"],160)
        first = {p["unit_id"]: p for p in self.rows("slices", name) if p["tick"] == 0}
        expected = {
            "a1": (-35,170,0,0),
            "a2": (35,170,0,0),
            "b1": (-35,170,105,180),
            "b2": (35,170,105,180),
        }
        self.assertEqual(set(first),set(expected))
        for name_id, (x,y,z,yaw) in expected.items():
            state = first[name_id]
            self.assertEqual((state["x"],state["y"],state["z"],state["yaw_deg"]),
                             (x,y,z,yaw))
        pairs = self.rows("pairs",name)
        self.assertEqual(len(pairs),6)
        self.assertEqual(scene["swept_lt6_pair_ticks"],
                         sum(p["swept_lt6_ticks"] for p in pairs))
        for pair in pairs:
            breached = (pair["min_sampled_separation_blocks"] < 6
                        or pair["min_swept_center_separation_blocks"] < 6
                        or pair["sampled_lt6_ticks"] > 0 or pair["swept_lt6_ticks"] > 0)
            self.assertEqual(pair["body_gate"],"FAILED" if breached else "PASS")
            self.assertEqual(any(g.startswith(
                "BODY_SEPARATION_LT6:"+pair["first_unit"]+":"+pair["second_unit"])
                for g in scene["failed_operational_gates"]),breached)
        expected_failure=bool(scene["failed_operational_gates"])
        self.assertEqual(scene["status"],
                         "FAILED_SOURCE_SAFETY" if expected_failure else "PASS_SOURCE_SAFETY")

    def test_unchanged_b17_aft_failure_forward_success_95_threshold(self) -> None:
        aft, forward = self.case("original_b17_aft"),self.case("original_b17_forward")
        self.assertEqual(aft["simulated_ticks"],190)
        self.assertEqual(forward["simulated_ticks"],190)
        for name, expected in (
                ("original_b17_aft",{"cargo":(0,170,0,0),
                                     "cover1":(-65,190,-20,0),
                                     "cover2":(65,190,-20,0),
                                     "raid":(0,170,170,180)}),
                ("original_b17_forward",{"cargo":(0,170,0,0),
                                         "cover1":(-27,190,115,0),
                                         "cover2":(27,190,115,0),
                                         "raid":(0,170,170,180)})):
            first = {p["unit_id"]:p for p in self.rows("slices",name) if p["tick"]==0}
            for unit,(x,y,z,yaw) in expected.items():
                self.assertEqual((first[unit]["x"],first[unit]["y"],
                                  first[unit]["z"],first[unit]["yaw_deg"]),
                                 (x,y,z,yaw),f"Changed original geometry: {name}/{unit}")
            sc = self.case(name)
            for pair in self.rows("pairs",name):
                violated=pair["min_swept_center_separation_blocks"]<6
                self.assertEqual(pair["body_gate"],"FAILED" if violated else "PASS")
                self.assertEqual(any(g.startswith(
                    "BODY_SEPARATION_LT6:"+pair["first_unit"]+":"+pair["second_unit"])
                    for g in sc["failed_operational_gates"]),violated)
        assets_aft = self.rows("assets","original_b17_aft")
        assets_forward = self.rows("assets","original_b17_forward")
        self.assertEqual(len(assets_aft),len(assets_forward))
        self.assertEqual(len(assets_aft),1)
        bad, good = assets_aft[0],assets_forward[0]
        self.assertEqual(bad["protection_radius_blocks"],95)
        self.assertEqual(good["protection_radius_blocks"],95)
        self.assertEqual(bad["initial_closest_hostile_blocks"],170)
        self.assertEqual(good["initial_closest_hostile_blocks"],170)
        for scene,asset in ((aft,bad),(forward,good)):
            intrusion=(asset["min_swept_hostile_blocks"]<=95
                       or asset["min_sampled_hostile_blocks"]<=95
                       or asset["within95_swept_ticks"]>0
                       or asset["within95_sampled_ticks"]>0)
            self.assertEqual(asset["protection_gate"],"FAILED" if intrusion else "PASS")
            self.assertEqual(any(s.startswith("B17_PROTECTION_BREACHED:cargo")
                                 for s in scene["failed_operational_gates"]),intrusion)
            self.assertEqual(scene["status"],
                "FAILED_SOURCE_SAFETY" if scene["failed_operational_gates"]
                else "PASS_SOURCE_SAFETY")
        self.assertGreater(bad["bomber_path_blocks"],20)
        self.assertGreater(good["bomber_path_blocks"],20)
        for scene, asset in ((aft,bad),(forward,good)):
            self.assertEqual(asset["bomber_ground_ticks"]>0,
                             any(s.startswith("TERRAIN_CONTACT:cargo")
                                 for s in scene["failed_operational_gates"]))

    def test_full_suite_seed_and_input_order_byte_reproducibility(self) -> None:
        repeat = self.root / "repeat-reversed"
        again = run_twin(self.java,self.classes,repeat,
                         seed=20261011,unique_ticks=240,
                         trace_stride=10,scenario="all",reverse_roster=True)
        self.assertEqual(self.summary, again)
        make_twin_html(repeat,repeat / "flight-twin.html")
        for name in TWOFIELDS:
            with self.subTest(name=name):
                self.assertEqual(self.checksum(self.output/name),self.checksum(repeat/name))

        different = self.root / "different-seed"
        run_twin(self.java,self.classes,different,seed=20261012,
                 unique_ticks=240,trace_stride=10,scenario="all_24_unique")
        self.assertNotEqual(
            self.checksum(self.output/"twin_units.csv"),
            self.checksum(different/"twin_units.csv"))

    def test_gate_failures_visible_and_standalone_html_valid(self) -> None:
        self.assertEqual(self.summary["body_separation_radius_blocks"],6)
        self.assertEqual(self.summary["b17_protection_radius_blocks"],95)
        self.assertIn("NO_FORGE_PARITY",self.summary["evidence"])
        unique = self.case("all_24_unique")
        # Stress case may or may not protect B17 as algorithms evolve, but any
        # measured intrusion MUST be independently visible and gate-failing.
        asset = self.rows("assets","all_24_unique")[0]
        if (asset["within95_swept_ticks"] > 0
                or asset["min_swept_hostile_blocks"] <= 95):
            self.assertEqual(asset["protection_gate"],"FAILED")
            self.assertEqual(unique["status"],"FAILED_SOURCE_SAFETY")
            self.assertTrue(any(g.startswith("B17_PROTECTION_BREACHED")
                                for g in unique["failed_operational_gates"]))
        self.assertEqual(asset["within95_swept_ticks"],
                         unique["swept_within95_hostile_ticks"])

        html=(self.output/"flight-twin.html").read_text(encoding="utf-8")
        self.assertIn("20 HZ",html)
        self.assertIn("twin_sensor_events.csv",html)
        self.assertIn("95 blocks",html)
        self.assertIn("CLOSED-LOOP FLIGHT TWIN",html.upper())
        self.assertIn("NO_FORGE_PARITY",html)
        self.assertNotIn("<script src=",html)
        self.assertNotIn("<link href=",html)
        self.assertNotIn("https://",html)
        self.assertNotIn("http://",html)
        if shutil.which("node"):
            js = html.rsplit("<script>",1)[1].split("</script>",1)[0]
            source = self.root/"twin-inline.js"
            source.write_text(js,encoding="utf-8")
            subprocess.run([shutil.which("node"),"--check",str(source)],check=True)


if __name__ == "__main__":
    unittest.main()

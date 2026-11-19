#!/usr/bin/env python3
"""Forensic acceptance and provenance guards for original REAL Forge B17 receipts.

The original per-entity Forge CSV is ignored, read-only, and cannot be
reconstructed in CI from SOURCE; skip REAL-only tests when it is absent.
When present, the tests demand the real 5x341 control samples, synchronized
game clocks, geometry sidecar crosschecks, trustworthy source labels,
unchanged 6b/95b gates, and reproducible JDK17 closed-loop Twin output.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from forensic_b17_compare import (
    DEFAULT_REAL, DEFAULT_MANIFEST, ForensicEvidenceError,
    GEOMETRY_SCHEMA, REAL_TICK_COUNT, UNITS,
    load_verified_real, load_source_twin, run_forensic, make_forensic_html,
)
from flight_lab_run import get_java17, MODULE


class OriginalForgeB17Forensics(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DEFAULT_REAL.is_dir():
            raise unittest.SkipTest(
                "Original ignored REAL Forge B17 CSV not available; no forged fixture substituted")
        cls.javac, cls.java = get_java17()
        cls.temp = tempfile.TemporaryDirectory(prefix="ww-b17-real-forensic-tests-")
        cls.root = Path(cls.temp.name)
        cls.base = cls.root / "base"
        cls.report, cls.frames, cls.controls, cls.events = run_forensic(
            DEFAULT_REAL,cls.base,seed=20261011)
        make_forensic_html(cls.base,cls.report,cls.frames,cls.controls,cls.events)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    @staticmethod
    def checksum(file: Path) -> str:
        return hashlib.sha256(file.read_bytes()).hexdigest()

    def test_live_sensor_contract_against_readonly_original_runtime_java(self) -> None:
        source = (MODULE/"runtime-probe"/"src"/"main"/"java"/"org"
                  /"kneekura"/"techhub"/"warfarewings"/"trace"/"LiveAirSensor.java")
        java = source.read_text(encoding="utf-8")
        range_match = re.search(r"DEFAULT_RANGE\s*=\s*([0-9.]+)\s*;",java)
        full_fov_match = re.search(r"DEFAULT_FULL_FOV_DEG\s*=\s*([0-9.]+)\s*;",java)
        self.assertIsNotNone(range_match)
        self.assertIsNotNone(full_fov_match)
        self.assertEqual(float(range_match.group(1)),240.0)
        self.assertEqual(float(full_fov_match.group(1)),150.0)
        self.assertEqual(self.report["source_twin_evidence"]["sensor"]["range_blocks"],
                         float(range_match.group(1)))
        self.assertEqual(
            self.report["source_twin_evidence"]["sensor"]["fov_half_angle_degrees"],
            float(full_fov_match.group(1))/2)
        self.assertEqual(
            self.report["source_twin_evidence"]["sensor"]["terrain_samples"],24)
        self.assertIn("NO_FORGE_PARITY",self.report["source_twin_evidence"]["evidence"])

    def test_strict_real_provenance_complete_340tick_clock_and_geometry(self) -> None:
        data = load_verified_real(DEFAULT_REAL,DEFAULT_MANIFEST)
        self.assertEqual(data.sidecar,self.report["real_evidence"]["original_340tick_summary"])
        self.assertEqual(data.sidecar["observed_aircraft"],5)
        self.assertEqual(data.sidecar["observed_ticks"],340)
        self.assertEqual(len(data.geometry),341)
        self.assertEqual(data.geometry_extra_sample,1)
        self.assertEqual(len(self.frames),REAL_TICK_COUNT+1)
        self.assertEqual(len(self.controls),len(UNITS)*(REAL_TICK_COUNT+1))
        self.assertEqual(self.frames[0]["real_game_time"],data.game_time_zero)
        for name in UNITS:
            self.assertEqual(len(data.traces[name]),341)
            self.assertEqual(data.traces[name][-1]["tick"],340)
        self.assertEqual(self.frames[-1]["real_game_time"],data.game_time_zero+340)
        self.assertEqual(self.report["real_evidence"]["class"],
                         "ACTUAL_SYNCHRONIZED_MINECRAFT_ENTITY_POSITIONS")
        self.assertEqual(self.report["source_twin_evidence"]["case_summary"]["active_aircraft"],5)
        self.assertEqual(self.report["comparison_contract"]["ticks_compared"],341)

    def test_original_start_geometry_and_gate_are_not_rewritten(self) -> None:
        init = {u:next(p for p in self.controls if p["tick"]==0 and p["unit_id"]==u)
                for u in UNITS}
        expected = {
            "b17":(0,165,0),
            "escort-left":(-48,172,18),"escort-right":(48,172,18),
            "raider-1":(-40,168,148),"raider-2":(40,168,153)
        }
        for id,xyz in expected.items():
            a = init[id]
            self.assertAlmostEqual(a["real_x_aligned"],xyz[0],places=6)
            self.assertAlmostEqual(a["real_y"],xyz[1],places=6)
            self.assertAlmostEqual(a["real_z_aligned"],xyz[2],places=6)
            self.assertEqual((a["source_x"],a["source_y"],a["source_z"]),xyz)
        agg=self.report["aggregate"]
        real=self.report["real_evidence"]["original_340tick_summary"]
        self.assertEqual(self.report["comparison_contract"]["body_separation_blocks"],6)
        self.assertEqual(self.report["comparison_contract"]["b17_protection_blocks"],95)
        self.assertAlmostEqual(agg["real_forge_min_b17_raider_blocks"],
                               real["protected_assets"][0]["closest_hostile_blocks"],places=5)
        self.assertEqual(agg["real_forge_strict_inside_95_ticks"],
                         real["protected_assets"][0]["hostile_inside_95_blocks_ticks"])
        self.assertEqual(agg["real_protection_failed"],
                         bool(real["failed_operational_gates"]))
        self.assertEqual(agg["source_protection_failed"],
                         self.report["source_twin_evidence"]["source_b17_asset"]["protection_gate"]
                         == "FAILED")
        self.assertEqual(agg["real_forge_sampled_lt6_pair_ticks"],
                         sum(p["under_6_blocks_ticks"] for p in real["pairs"]))
        self.assertEqual(len(self.report["pairs"]),10)
        self.assertEqual(agg["comparison_is_real_parity_gate"],"NOT_A_PARITY_VERDICT")

    def test_95b_entry_timelines_sightings_maneuvers_and_event_provenance(self) -> None:
        first_real=next(f["tick"] for f in self.frames if f["real_forge_inside_or_touch_95"])
        first_source=next(f["tick"] for f in self.frames if f["source_twin_inside_or_touch_95"])
        self.assertGreater(first_real,0)
        self.assertGreater(first_source,0)
        self.assertNotEqual(self.frames[first_real]["tick_explanation"],"")
        self.assertTrue(any(e["tick"]==first_real and e["channel"]=="REAL_FORGE"
                            and e["event"]=="B17_95_ENTER" for e in self.events))
        self.assertTrue(any(e["tick"]==first_source and e["channel"]=="SOURCE_TWIN"
                            and e["event"]=="B17_95_ENTER" for e in self.events))
        self.assertTrue(any(e["event"]=="REAL_PHASE_CHANGE" for e in self.events))
        self.assertTrue(any(e["event"]=="TWIN_VISIBILITY_CHANGE" for e in self.events))
        self.assertTrue(any(e["event"]=="TWIN_MANEUVER_CHANGE" for e in self.events))
        self.assertTrue(all(e["channel"] in ("REAL_FORGE","SOURCE_TWIN")
                            for e in self.events))
        self.assertTrue(all("SOURCE" in r["source_evidence"]
                            and "REAL" in r["real_evidence"]
                            and "NOT_A_TEACHER_FORCED_PARITY" in r["causal_note"]
                            for r in self.controls))
        self.assertEqual({r["unit_id"] for r in self.controls},set(UNITS))
        self.assertTrue(all(r["real_phase"] not in ("",None) and
                            r["source_inferred_phase"].startswith("SOURCE_")
                            for r in self.controls))

    def test_first_real_physics_tick_matches_initial_neutral_not_same_tick_ai(self) -> None:
        """All 5 REAL t1 physical motions precede the source END-t1 decisions."""
        for unit in UNITS:
            tick1=next(row for row in self.controls if row["tick"]==1 and row["unit_id"]==unit)
            tick2=next(row for row in self.controls if row["tick"]==2 and row["unit_id"]==unit)
            self.assertLess(tick1["combined_position_delta_blocks"],1e-5,
                            f"t1 {unit} must be physical initial neutral flight")
            self.assertEqual(tick1["source_applied_control_x"],0)
            self.assertEqual(tick1["source_applied_control_z"],0)
            self.assertEqual(tick1["source_applied_control_throttle"],1)
            self.assertEqual(tick1["source_applied_control_from_policy_tick"],-1)
            self.assertEqual(tick1["source_command_generated_at_end_tick"],1)
            self.assertAlmostEqual(tick2["source_applied_control_x"],
                                   tick1["source_control_x"],places=9)
            self.assertAlmostEqual(tick2["source_applied_control_z"],
                                   tick1["source_control_z"],places=9)
            self.assertAlmostEqual(tick2["source_applied_control_throttle"],
                                   tick1["source_control_throttle"],places=9)
            self.assertEqual(tick2["source_applied_control_from_policy_tick"],1)

    def test_reversed_roster_seed_repeats_every_report_byte_for_byte(self) -> None:
        second=self.root/"repeat"
        again,ticks,controls,events=run_forensic(
            DEFAULT_REAL,second,seed=20261011,reverse_roster=True)
        make_forensic_html(second,again,ticks,controls,events)
        self.assertEqual(self.report,again)
        report_names=[
            "forensic_b17_summary.json","forensic_b17_ticks.csv","forensic_b17_controls.csv",
            "forensic_b17_events.csv","forensic_b17_units.csv","forensic_b17_pairs.csv",
            "forensic_b17_findings.md","forensic_b17.html",
            "twin_summary.json","twin_units.csv","twin_pairs.csv","twin_assets.csv",
            "twin_time_slices.csv","twin_sensor_events.csv"
        ]
        for file in report_names:
            with self.subTest(file=file):
                self.assertEqual(self.checksum(self.base/file),self.checksum(second/file))

    def test_incomplete_real_source_never_promoted(self) -> None:
        truncated=(MODULE/"runtime-probe"/"run-gametest"/"pre-margin2-root")
        if truncated.is_dir():
            with self.assertRaisesRegex(ForensicEvidenceError,
                                        "Independent REAL Forge receipt validation FAILED"):
                load_verified_real(truncated)

    def test_tampered_forge_header_source_and_geometry_fail_closed(self) -> None:
        tampered = self.root/"tampered-real"
        shutil.copytree(DEFAULT_REAL,tampered)
        file=tampered/"op-b17-forge-controls.csv"
        content=file.read_text(encoding="utf-8")
        self.assertIn("minecraft_runtime_ia_next_tick_injection",content)
        file.write_text(content.replace("minecraft_runtime_ia_next_tick_injection",
                                        "SOURCE_SIMULATOR_FAKE",1),encoding="utf-8")
        with self.assertRaisesRegex(ForensicEvidenceError,
                                    "Independent REAL Forge receipt validation FAILED"):
            load_verified_real(tampered)
        shutil.copy2(DEFAULT_REAL/file.name,file)
        geometry=tampered/"operational-b17-escort-geometry.csv"
        rows=geometry.read_text(encoding="utf-8")
        self.assertIn("55.500093155",rows)
        geometry.write_text(rows.replace("55.500093155","55.600093155",1),
                            encoding="utf-8")
        with self.assertRaisesRegex(ForensicEvidenceError,
                                    "Independent REAL geometry mismatches"):
            load_verified_real(tampered)

    def test_duplicate_tick_or_cross_aircraft_clock_is_rejected(self) -> None:
        tampered=self.root/"broken-clock"
        shutil.copytree(DEFAULT_REAL,tampered)
        trace=tampered/"op-raider-2-forge-controls.csv"
        with trace.open(newline="",encoding="utf-8") as src:
            reader=csv.DictReader(src)
            headers=reader.fieldnames
            rows=list(reader)
        self.assertEqual(len(rows),341)
        original=rows[88]["sim_tick"]
        rows[88]["sim_tick"]=rows[87]["sim_tick"]
        with trace.open("w",newline="",encoding="utf-8") as out:
            writer=csv.DictWriter(out,fieldnames=headers,lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ForensicEvidenceError,
                                    "Independent REAL Forge receipt validation FAILED"):
            load_verified_real(tampered)
        rows[88]["sim_tick"]=original
        rows[88]["game_time"]=rows[87]["game_time"]
        with trace.open("w",newline="",encoding="utf-8") as out:
            writer=csv.DictWriter(out,fieldnames=headers,lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ForensicEvidenceError,
                                    "Independent REAL Forge receipt validation FAILED"):
            load_verified_real(tampered)

    def test_twin_laundering_real_evidence_is_rejected(self) -> None:
        copied = self.root/"forged-source"
        copied.mkdir(parents=True,exist_ok=True)
        for filename in ("twin_summary.json","twin_units.csv","twin_pairs.csv",
                         "twin_assets.csv","twin_time_slices.csv",
                         "twin_sensor_events.csv"):
            shutil.copy2(self.base/filename,copied/filename)
        summary_file=copied/"twin_summary.json"
        raw=json.loads(summary_file.read_text(encoding="utf-8"))
        raw["evidence"]="ACTUAL_SYNCHRONIZED_MINECRAFT_ENTITY_POSITIONS"
        summary_file.write_text(json.dumps(raw),encoding="utf-8")
        with self.assertRaisesRegex(ForensicEvidenceError,"NO_FORGE_PARITY"):
            load_source_twin(copied)

    def test_stale_archive_sidecar_requires_explicit_quarantine(self) -> None:
        newer=MODULE/"runtime-probe"/"run-gametest"/"pre-cpa-original-root"
        if not newer.is_dir():
            self.skipTest("Optional newer REAL flight receipts are absent")
        with self.assertRaisesRegex(ForensicEvidenceError,
                                    "sidecar disagrees"):
            load_verified_real(newer)
        validated=load_verified_real(newer,quarantine_stale_sidecar=True)
        self.assertEqual(validated.saved_sidecar_status,
                         "STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED")
        self.assertEqual(validated.sidecar["schema_version"],
                         "ww.physics.forge-multiaircraft-acceptance.v1")
        self.assertEqual(validated.sidecar["source"],
                         "minecraft_runtime_ia_next_tick_injection")
        self.assertEqual(len(validated.traces["b17"]),341)

    def test_self_contained_forensics_visualization_and_readonly_real(self) -> None:
        html=(self.base/"forensic_b17.html").read_text(encoding="utf-8")
        self.assertIn("REAL_FORGE",html)
        self.assertIn("SOURCE_TWIN",html)
        self.assertIn("340-tick B-17",html)
        self.assertIn("forensic_b17",html)
        self.assertNotIn("<script src=",html)
        self.assertNotIn("https://",html)
        self.assertNotIn("http://",html)
        if shutil.which("node"):
            js=html.rsplit("<script>",1)[1].split("</script>",1)[0]
            path=self.root/"b17-forensic-inline.js"
            path.write_text(js,encoding="utf-8")
            subprocess.run([shutil.which("node"),"--check",str(path)],check=True)
        for filename,old_hash in self.report["real_evidence"][
                "sha256_by_original_readonly_filename"].items():
            origin=(DEFAULT_MANIFEST if filename==DEFAULT_MANIFEST.name
                    else DEFAULT_REAL/filename)
            self.assertEqual(self.checksum(origin),old_hash)


if __name__ == "__main__":
    unittest.main()

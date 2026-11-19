#!/usr/bin/env python3
"""Static parser/security regression fixtures; never authorizes projectiles."""

import tempfile
import unittest
from pathlib import Path

from audit_exact_weapon_failclosed import audit_no_fire_frame, digest, method_block


class WeaponAuditParserTests(unittest.TestCase):
    @staticmethod
    def source_frame(*, ally: bool = False, firing: str = "false",
                     projectile_speed: str = "0") -> str:
        arguments = [f"arg{i}" for i in range(12)] + [firing, projectile_speed]
        if ally:
            arguments.append("observedLeaderVelocity")
        return "var frame = new TacticalAirAI.Frame(\n  " + ",\n  ".join(arguments) + "\n);\n"

    def test_legacy_explicit_false_zero_fire_gate_is_accepted(self):
        self.assertEqual(audit_no_fire_frame(self.source_frame()), 1)

    def test_explicit_friendly_velocity_does_not_disable_weapon_audit(self):
        self.assertEqual(audit_no_fire_frame(self.source_frame(ally=True)), 1)

    def test_real_current_pilot_passes_both_no_fire_fields(self):
        source = (Path(__file__).resolve().parent.parent / "runtime-probe" /
                  "src/main/java/org/kneekura/techhub/warfarewings/trace/RuntimeTacticalPilot.java")
        if not source.is_file():
            # The pinned, no-network SOURCE Docker image deliberately does
            # not include runtime-probe/Minecraft. Local owner/Hosted source
            # checks do require this real adapter; never substitute a fake
            # source file for the security gate in an isolated container.
            self.skipTest("Actual Forge adapter intentionally excluded from SOURCE-only Docker image")
        self.assertEqual(audit_no_fire_frame(source.read_text(encoding="utf-8")), 1)

    def test_true_fire_permission_is_rejected_even_if_second_frame_safe(self):
        source = self.source_frame(ally=True) + self.source_frame(firing="true")
        with self.assertRaisesRegex(ValueError, "enables/obscures"):
            audit_no_fire_frame(source)

    def test_nonzero_or_expression_projectile_speed_is_rejected(self):
        for unsafe in ("2.5", "projectileSpeedBpt", "0 + 1"):
            with self.subTest(unsafe=unsafe), self.assertRaisesRegex(ValueError, "enables/obscures"):
                audit_no_fire_frame(self.source_frame(projectile_speed=unsafe))

    def test_no_real_live_frame_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "No live Forge"):
            audit_no_fire_frame("// new TacticalAirAI.Frame(...);\n")

    def test_existing_direct_original_fire_entry_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError, "Direct original weapon API"):
            audit_no_fire_frame(self.source_frame(ally=True) + "\nplane.fireWeapon(0, 0, aim);\n")

    def test_extracts_only_requested_server_fire_method(self):
        sample = """Compiled from \"X.java\"
  public void fire(org.joml.Vector3f);
    Code:
       0: invokevirtual #1  // Method spentAmmo:(Ljava/util/Map;I)Z
       1: invokevirtual #2  // Method immersive_aircraft/entity/weapon/BulletWeapon.fire:(Lorg/joml/Vector3f;)V
       2: return
  public void clientFire(int);
    Code:
       0: invokevirtual #3  // Method clientOnlyCoolDown:()V
       1: return
"""
        body = method_block(sample, "void fire(org.joml.Vector3f);")
        self.assertIn("spentAmmo", body)
        self.assertIn("BulletWeapon.fire", body)
        self.assertNotIn("clientOnlyCoolDown", body)

    def test_unknown_fire_signature_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing/changed"):
            method_block("  public void fire(java.lang.Object);\n    Code:\n       0: return\n",
                         "void fire(org.joml.Vector3f);")

    def test_mismatched_binary_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not-an-original-jar"
            path.write_bytes(b"fake public jar")
            with self.assertRaisesRegex(ValueError, "Pinned sha256 mismatch"):
                digest(path, "sha256", "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43")


if __name__ == "__main__":
    unittest.main(verbosity=2)

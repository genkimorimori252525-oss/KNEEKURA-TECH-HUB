#!/usr/bin/env python3
"""Static parser/security regression fixtures; never authorizes projectiles."""

import tempfile
import unittest
from pathlib import Path

from audit_exact_weapon_failclosed import digest, method_block


class WeaponAuditParserTests(unittest.TestCase):
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

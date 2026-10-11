#!/usr/bin/env python3
"""Verify pinned binary weapon callpaths without enabling autonomous fire.

An observed ammo-consuming fire method is *not* proof of legal installed
mounts, server cooldown, friend LOS, projectile owner or kill attribution.
No amount of bytecode pattern matching may promote the AI's fire permission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

WW_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
IA_SHA512 = "7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055"
WW_MG = "net.velleagle.warfare_wings.entity.weapon.WarfareWingsMG"
WW_BOMB = "net.velleagle.warfare_wings.entity.weapon.WarfareWingsBombBay"
IA_VEHICLE = "immersive_aircraft.entity.InventoryVehicleEntity"


def digest(path: Path, algorithm: str, expected: str) -> None:
    checksum = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    if checksum.hexdigest() != expected:
        raise ValueError(f"Pinned {algorithm} mismatch; refusing substituted binary: {path.name}")


def method_block(disassembled: str, signature: str) -> str:
    pattern = r"(?m)^  (?:public|protected|private) (?:\S+ )?" + re.escape(signature) + r"\s*\n\s*Code:\s*\n"
    hit = re.search(pattern, disassembled)
    if hit is None:
        raise ValueError(f"Pinned weapon API missing/changed: {signature}")
    tail = disassembled[hit.end():]
    next_method = re.search(r"(?m)^  (?:public|protected|private) (?:\S+ )?\S+\(.*\);\s*$", tail)
    return tail[:next_method.start()] if next_method else tail


def audit(ww: Path, ia: Path, javap: str, pilot_source: Path | None = None) -> dict:
    digest(ww, "sha256", WW_SHA256)
    digest(ia, "sha512", IA_SHA512)

    def disassemble(binary: Path, classname: str) -> str:
        proc = subprocess.run([javap, "-c", "-p", "-classpath", str(binary), classname],
                              check=True, capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        return proc.stdout

    mg = method_block(disassemble(ww, WW_MG), "void fire(org.joml.Vector3f);")
    bomb = method_block(disassemble(ww, WW_BOMB), "void fire(org.joml.Vector3f);")
    ia_fire = method_block(disassemble(ia, IA_VEHICLE),
                           "void fireWeapon(int, int, org.joml.Vector3f);")
    if not ("spentAmmo:" in mg and "BulletWeapon.fire:" in mg
            and "spentAmmo:" in bomb and "BulletWeapon.fire:" in bomb
            and "Weapon.fire:" in ia_fire and "java/util/List.get:" in ia_fire):
        raise ValueError("Unexpected original binary fire/ammo/slot callpath changed")
    with zipfile.ZipFile(ww) as archive:
        classnames = tuple(archive.namelist())
    torpedo_classes = [name for name in classnames if name.endswith(".class")
                       and "torpedo" in name.lower()]
    no_fire_runtime_verified = False
    if pilot_source is not None:
        actual_pilot = pilot_source.read_text(encoding="utf-8")
        if (re.search(r"new\s+TacticalAirAI\.Frame\s*\(.*?\bsurface\s*,\s*false\s*,\s*0\s*\)",
                      actual_pilot, re.S) is None
                or re.search(r"\.\s*fireWeapon\s*\(|\.\s*fire\s*\(\s*new\s+Vector3f", actual_pilot)):
            raise ValueError("Exact live Forge pilot no-fire control contract changed")
        no_fire_runtime_verified = True
    # Complete evidence of a safe AI launch requires observing the actual
    # inventory mounts and ammunition *in each entity*, a separate enforced
    # server timer and phase/LOS/friend corridor, plus damage/owner proof.
    # Those are not established by these static fire entrypoint signatures.
    return {
        "schema_version": "ww.physics.exact-weapon-audit.v1",
        "warfare_wings_sha256": WW_SHA256,
        "immersive_aircraft_sha512": IA_SHA512,
        "mg_fire_consumes_ammo_before_bullet_fire": True,
        "bomb_fire_consumes_ammo_before_bullet_fire": True,
        "ia_server_fire_dispatches_slot_index_without_proven_mission_guard": True,
        "original_ww_torpedo_named_classes": torpedo_classes,
        "live_ai_no_fire_frame_source_verified": no_fire_runtime_verified,
        "installed_slot_mounts_verified": False,
        "server_cooldown_enforced_for_autonomous_pilot": False,
        "allied_air_and_ground_muzzle_corridor_verified": False,
        "projectile_ownership_and_kill_attribution_verified": False,
        "autonomous_mg_fire_enabled": False,
        "autonomous_bomb_release_enabled": False,
        "autonomous_torpedo_release_enabled": False,
        "conclusion": "FAIL_CLOSED_NO_AUTONOMOUS_WEAPONS_AUTHORIZED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ww", type=Path, required=True)
    parser.add_argument("--ia", type=Path, required=True)
    parser.add_argument("--javap", default="javap")
    parser.add_argument("--pilot-source", type=Path,
                        help="verify runtime adapter still enforces false/zero gun authorization")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.ww, args.ia, args.javap, args.pilot_source)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"EXACT_WEAPON_AUDIT_FAILED: {exc}") from None
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

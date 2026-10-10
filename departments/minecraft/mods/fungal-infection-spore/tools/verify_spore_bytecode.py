#!/usr/bin/env python3
"""Verify selected original Spore 2.2.0j JAR bytecode contracts. No game launch."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

JAR_SHA = "d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489"
ROOT = "com/Harbinger/Spore/"
CLASS_SHA = {
    "Sentities/Organoids/Proto": "8ab88d4e784512d910643831d8ec2caaeb4b9acf15a319a28752a3b9c5fcade3",
    "sEvents/HandlerEvents": "632fcefca9b8cbad565fbda408bda3b2a1d73951efc01049844cb4dacdbf3805",
    "Sentities/BaseEntities/Organoid": "bef7703f12a8d06028dfd8a4b72d959b6303b94e17bbb164cb407eefcb7c163f",
    "ExtremelySusThings/SporeSavedData": "c20be21c37d0806c7f84c61f5867f0872de7ff10a99faa8ba11ff9e1798db1e7",
    "ExtremelySusThings/ChunkLoaderHelper": "c36a94ef283cdeb23e98ad6aa157d34b29d74cff908490f35fbfcbca7dd78d55",
    "ExtremelySusThings/ChunkLoadRequest": "3f55f0d1b6c61ef2f1a884723c9136b3017baf8ac11b190cc6f0994434dd059e",
    "Sentities/Organoids/Womb": "7ac7824e6164b688caf695976bb892473014d377f99a9151daa2a1ccec213ccc",
    "Sentities/AI/NeuralProcessing/ProtoAIs/ProtoTargeting": "a12fa4539b2721057b0f01d506aa4fa92a6dfbe0a93c32278bfbffc0585ab2ba",
    "Core/SConfig$Server": "11eb1371ed17b8fc34e6e462551090a373064096677fb8b144c57ea52b25240d",
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(2 * 1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def method(javap_output, name):
    lines = javap_output.splitlines()
    def declaration(line):
        return (line.startswith("  ") and not line.startswith("    ")
                and re.match(r"  (public|protected|private|static)\b", line)
                and line.endswith(";") and "(" in line)
    start = next((i for i, line in enumerate(lines) if declaration(line)
                  and re.search(r"\b" + re.escape(name) + r"\(", line)), None)
    if start is None:
        raise RuntimeError("missing method " + name)
    end = next((i for i in range(start + 1, len(lines)) if declaration(lines[i])), len(lines))
    return "\n".join(lines[start:end])


def matches(text, pattern):
    return bool(re.search(pattern, text, re.MULTILINE | re.DOTALL))


def verify(jar):
    actual = sha(jar)
    if actual != JAR_SHA:
        return {"status": "BLOCKED_HASH_MISMATCH", "artifact_sha256": actual, "expected_sha256": JAR_SHA}
    with zipfile.ZipFile(jar) as z:
        pins = {ROOT + cls + ".class": hashlib.sha256(z.read(ROOT + cls + ".class")).hexdigest()
                for cls in CLASS_SHA}
    if any(pins[ROOT + cls + ".class"] != expected for cls, expected in CLASS_SHA.items()):
        return {"status": "BLOCKED_CLASS_HASH_MISMATCH", "artifact_sha256": actual}
    dumps = {}
    for cls in CLASS_SHA:
        binary_name = (ROOT + cls).replace("/", ".")
        result = subprocess.run(["javap", "-p", "-c", "-constants", "-classpath", str(jar), binary_name],
                                capture_output=True, text=True, check=True)
        dumps[cls] = result.stdout
    p = dumps["Sentities/Organoids/Proto"]
    e = dumps["sEvents/HandlerEvents"]
    s = dumps["ExtremelySusThings/SporeSavedData"]
    cr = dumps["ExtremelySusThings/ChunkLoadRequest"]
    spawn = method(p, "summonMob")
    feedback = method(e, "DefenseBypass")
    feedback_branch = feedback[feedback.index("1243:"):feedback.index("1442:")]
    tick = method(p, "m_8119_")
    update = method(p, "adjustWeightsForDecision")
    morale = method(p, "moraleBoost")
    codechecks = {
        "sampled_index_differs_from_member_tag": matches(spawn, r"RandomSource\.m_188503_.*?istore\s+4.*?iload\s+4.*?entityResourceLocation") and matches(spawn, r"// String member\n\s*\d+: iload_1") and matches(spawn, r"// String decision\n\s*\d+: iload_1"),
        "four_candidates_per_team_default": all(x in method(p, "fillDefaultTeams") for x in ("iconst_4", "Collections.shuffle", "List.add")),
        "damage_event_praises_and_punishes": all(x in feedback_branch for x in ("String hivemind", "String decision", "String member", "Proto.praisedForDecision", "Proto.punishForDecision", "Level.m_6815_")),
        "feedback_not_scaled_by_damage_amount": "LivingDamageEvent.getAmount" not in feedback_branch and "Proto.praisedForDecision" in feedback_branch,
        "reward_and_penalty_deltas": "double 0.05d" in method(p, "praisedForDecision") and "double -0.1d" in method(p, "punishForDecision"),
        "ordinary_row_update_clamps": all(x in update for x in ("iconst_4", "java/lang/Math.min", "java/lang/Math.max")),
        "deterministic_argmax_and_fixed_null_features": "Method argmax:([D)I" in method(p, "decide") and "ifnonnull" in method(p, "inputs"),
        "morale_additive_unclamped": "RandomSource.m_188500_" in morale and "dadd" in morale and "java/lang/Math.min" not in morale and "java/lang/Math.max" not in morale,
        "multi_spawn_biomass_unbounded": all(x in tick for x in ("getBiomass", "iconst_5", "summonMob")) and "isub" in method(p, "eatBiomass") and "java/lang/Math.max" not in method(p, "eatBiomass"),
        "global_static_proto_count": "private static final java.util.List" in s and "Field protos" in method(s, "getAmountOfHiveminds") and "java/util/List.size" in method(s, "getAmountOfHiveminds"),
        "world_load_no_dimension_gate": "SporeSavedData.getRequests" in method(e, "onWorldLoad") and "ChunkLoaderHelper.forceChunk" in method(e, "onWorldLoad") and "getDimension" not in method(e, "onWorldLoad"),
        "ticket_containsValue_without_equals": "java/util/Map.containsValue" in method(p, "lambda$loadChunks$2") and not matches(cr, r"^  public boolean equals\("),
        "proto_join_leave_registry_hooks": "SporeSavedData.addProto" in method(e, "onLivingSpawned") and "SporeSavedData.removeProto" in method(e, "DiscardProto"),
    }
    return {
        "schema": "kneekura.spore.bytecode-gate.v1",
        "artifact_sha256": actual,
        "status": "PASS_STATIC_BYTECODE" if all(codechecks.values()) else "FAIL_STATIC_BYTECODE",
        "class_hashes_verified": len(pins),
        "contracts_passed": sum(codechecks.values()),
        "contracts_total": len(codechecks),
        "checks": codechecks,
        "conditional_deductions": {
            "team_members_uniform_four": "12/16 mismatched indices (75%), not necessarily distinct species",
            "two_hits_one_hit_taken_no_clamp": "+0.05 +0.05 -0.10 = 0",
            "nonnegative_expected_delta_exclusive_feedback": "P(positive) >= 2/3",
            "global_three_protos_two_dimensions": "2 in dimension A +1 in dimension B -> global count3, conditional on being registered",
        },
        "verification_scope": "JAR bytecode structures only; NO Forge launch, GameTest, TPS, AI effectiveness or fix-confirmation",
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("jar", type=Path, help="Locally owned Spore 2.2.0j JAR")
    cli.add_argument("--out", type=Path)
    opts = cli.parse_args()
    if not opts.jar.is_file():
        cli.error("missing JAR file")
    report = verify(opts.jar)
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if opts.out:
        opts.out.write_text(body, encoding="utf-8")
    else:
        print(body)
    return 0 if report["status"] == "PASS_STATIC_BYTECODE" else 1


if __name__ == "__main__":
    sys.exit(main())

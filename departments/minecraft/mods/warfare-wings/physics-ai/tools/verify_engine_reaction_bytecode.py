#!/usr/bin/env python3
"""Check all 24 engine reaction constants against the exact OWNER JAR bytecode.

Not a download utility: never logs, uploads or commits the binary. The static
Java opt-in catalog is accepted only when the input JAR has the exact SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

EXPECTED_SHA256 = "dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43"
DEFAULT_SOURCE = (Path(__file__).resolve().parent.parent / "src/main/java/"
                  "org/kneekura/techhub/warfarewings/physics/WarfareWingsEngineReaction.java")
BYTECODE_METHOD = re.compile(
    r"protected float getEngineReactionSpeed\(\);\s+Code:\s+"
    r"0:\s+(?:ldc(?:_w)?\s+\S+|sipush\s+\d+)"
    r"\s+// float (\d+(?:\.\d+)?)f\s+\d+: freturn",
    re.S,
)


def verified_catalog(source: Path) -> dict[str, int]:
    matches = re.findall(r'Map\.entry\("warfare_wings:([a-z0-9]+)",\s*(\d+)\)',
                         source.read_text(encoding="utf-8"))
    if len(matches) != 24 or len(set(m[0] for m in matches)) != 24:
        raise ValueError("expected 24 unique source-catalog entries")
    return {name: int(ticks) for name, ticks in matches}


def verify(jar: Path, javap: str, source: Path = DEFAULT_SOURCE) -> int:
    if not jar.is_file():
        raise ValueError("exact owner binary is absent")
    sha = hashlib.sha256(jar.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("wrong WARFARE WINGS SHA256; refusing another 1.1.4 binary")
    entries = verified_catalog(source)
    for name, expected in sorted(entries.items()):
        # Original bytecode really spells this one SPITFIREntity (no extra
        # uppercase E at the Entity join), unlike other BASEEntity names.
        simple = "SPITFIREntity" if name == "spitfire" else name.upper()+"Entity"
        clazz = f"net.velleagle.warfare_wings.entity.{simple}"
        proc = subprocess.run([javap, "-c", "-p", "-cp", str(jar), clazz],
                              text=True, capture_output=True, timeout=30,
                              check=True)
        match = BYTECODE_METHOD.search(proc.stdout)
        if not match:
            raise ValueError(f"{name}: exact class lacks readable getEngineReactionSpeed bytecode")
        actual = float(match.group(1))
        if actual != expected:
            raise ValueError(f"{name}: exact bytecode reaction {actual} vs catalog {expected}")
        print(f"PINNED_ENGINE_REACTION_OK warfare_wings:{name} {expected}ticks")
    print(f"EXACT_24_ENGINE_REACTIONS_VERIFIED owner-SHA256={sha}")
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--javap", required=True, help="absolute JDK 17 bin/javap path")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    verify(args.jar, args.javap, args.source)


if __name__ == "__main__":
    main()

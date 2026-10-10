#!/usr/bin/env python3
"""Reproduce the complete source-only physics suite using Java 17, Node and Python.

This suite makes no Minecraft parity claim and never opens external game artifacts.
All generated reports live in the OS temporary directory.
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def normalized_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip() + "\n"


def main() -> None:
    java_home = os.environ.get("JAVA_HOME", "")
    if not java_home:
        raise SystemExit("JAVA_HOME must identify the registered Java 17 JDK")
    java = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
    if not java.is_file():
        raise SystemExit(f"JAVA_HOME has no Java executable: {java}")
    java_version = subprocess.run([str(java), "-version"], check=True, text=True, capture_output=True)
    version_text = java_version.stderr + java_version.stdout
    print(version_text.strip(), flush=True)
    if 'version "17.' not in version_text and 'version "17"' not in version_text:
        raise SystemExit("Headless verification requires Java 17, not a newer JDK with --release 17")
    run("node", "--version")
    run(sys.executable, "--version")

    run("node", str(ROOT / "check-microkernel.mjs"), "--java-home", java_home)
    run(sys.executable, str(ROOT / "tools" / "test_compare_traces.py"))

    with tempfile.TemporaryDirectory(prefix="warfare-wings-atlas-") as directory:
        json_out = Path(directory) / "aircraft-atlas-ai-view.json"
        md_out = Path(directory) / "AIRCRAFT-ATLAS.md"
        run(
            sys.executable,
            str(ROOT / "tools" / "build_aircraft_atlas.py"),
            str(ROOT / "reports" / "base-aircraft-source-atlas.csv"),
            "--json", str(json_out),
            "--markdown", str(md_out),
        )
        golden_json = ROOT / "reports" / "aircraft-atlas-ai-view.json"
        if json.loads(json_out.read_text(encoding="utf-8")) != json.loads(golden_json.read_text(encoding="utf-8")):
            raise SystemExit("AI Atlas JSON semantic drift")
        golden_md = ROOT / "reports" / "AIRCRAFT-ATLAS.md"
        generated, expected = normalized_markdown(md_out), normalized_markdown(golden_md)
        if generated != expected:
            diff = "".join(difflib.unified_diff(
                expected.splitlines(True), generated.splitlines(True),
                fromfile="committed/AIRCRAFT-ATLAS.md", tofile="generated/AIRCRAFT-ATLAS.md", n=3,
            ))
            raise SystemExit("Aircraft Atlas Markdown drift:\n" + diff[:24000])

    print("HEADLESS_SOURCE_PASS: Java 17 invariants, deterministic traces, comparator and 24-aircraft Atlas")
    print("REAL_MINECRAFT_PARITY: NOT_RUN")


if __name__ == "__main__":
    main()

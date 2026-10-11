#!/usr/bin/env python3
"""Compile with JDK 17, run all-aircraft SOURCE batches, render offline HTML.

Use Python's standard library only. The compiled classes live in a temporary
directory; the chosen --output holds only scientific run outputs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from flight_lab_report import make_html, SCHEMA

MODULE = Path(__file__).resolve().parent.parent
MAIN = "org.kneekura.techhub.warfarewings.physics.FlightResearchBatchMain"


def java17_candidates(selected: Path | None = None) -> list[Path]:
    homes: list[Path] = []
    if selected is not None:
        homes.append(selected)
    for env_name in ("JAVA17_HOME", "JDK17_HOME"):
        if os.environ.get(env_name):
            homes.append(Path(os.environ[env_name]))
    if os.name == "nt":
        homes.extend([
            Path(r"C:\Program Files\Java\jdk-17"),
            Path(r"C:\Program Files\Eclipse Adoptium\jdk-17"),
        ])
    if os.environ.get("JAVA_HOME"):
        homes.append(Path(os.environ["JAVA_HOME"]))
    return homes


def get_java17(selected: Path | None = None) -> tuple[str, str]:
    suffix = ".exe" if os.name == "nt" else ""
    candidates = [(str(home / "bin" / ("javac" + suffix)),
                   str(home / "bin" / ("java" + suffix)))
                  for home in java17_candidates(selected)]
    if shutil.which("javac") and shutil.which("java"):
        candidates.append((shutil.which("javac"), shutil.which("java")))
    for javac, java in candidates:
        if not Path(javac).is_file() or not Path(java).is_file():
            continue
        try:
            version = subprocess.run([javac, "-version"], capture_output=True,
                                     text=True, check=True)
            runtime = subprocess.run([java, "-version"], capture_output=True,
                                     text=True, check=True)
            if re.search(r"\bjavac 17[.\s]", version.stdout + version.stderr) and \
               re.search(r'version "17[.\s]', runtime.stdout + runtime.stderr):
                return javac, java
        except (OSError, subprocess.CalledProcessError):
            continue
    raise RuntimeError(
        "A JDK 17 compiler and runtime are required. "
        "Pass --java-home PATH or set JAVA17_HOME (e.g. C:\\Program Files\\Java\\jdk-17)."
    )


def compile_lab(javac: str, classes: Path) -> None:
    source_dir = MODULE / "src" / "main" / "java" / "org" / "kneekura" / "techhub" / "warfarewings" / "physics"
    # Compile only the fixed pure-Java dependency graph. Forge integration and
    # concurrent physics-twin research may add classes needing different jars.
    dependency_names = (
        "Ia133Microkernel.java",
        "PinnedIa133WindWorld.java",
        "WarfareWingsAircraft.java",
        "WarfareWingsEngineReaction.java",
        "AircraftAtlasMain.java",
        "TacticalAirAI.java",
        "FlightGuidance.java",
        "FlightSafetyPlanner.java",
        "FlightControlLoop.java",
        "HistoricalDoctrineOrders.java",
        "FlightResearchBatchMain.java",
    )
    sources = [source_dir / filename for filename in dependency_names]
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing Java Flight Research Lab sources: {missing}")
    classes.mkdir(parents=True, exist_ok=True)
    subprocess.run([javac, "--release", "17", "-encoding", "UTF-8",
                    "-d", str(classes), *(str(p) for p in sources)],
                   cwd=MODULE, check=True)


def run_lab(java: str, classes: Path, output: Path, *,
            seed: int, trials_per_aircraft: int, ticks: int, trace_stride: int) -> dict:
    anchor = MODULE / "data" / "base-aircraft-anchor-v1.csv"
    output.mkdir(parents=True, exist_ok=True)
    command = [java, "-cp", str(classes), MAIN,
               str(anchor), str(output),
               "--seed", str(seed),
               "--trials-per-aircraft", str(trials_per_aircraft),
               "--ticks", str(ticks),
               "--trace-stride", str(trace_stride)]
    subprocess.run(command, cwd=MODULE, check=True)
    summary_file = output / "summary.json"
    with summary_file.open(encoding="utf-8") as stream:
        result = json.load(stream)
    if (result["schema"] != SCHEMA or result["aircraft_count"] != 24
            or result["trial_count"] != 24 * trials_per_aircraft
            or result["simulated_ticks"] != 24 * trials_per_aircraft * ticks
            or "NO_FORGE_PARITY" not in result["evidence"]):
        raise AssertionError("Unexpected model output identity or count")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Lab output folder")
    parser.add_argument("--java-home", type=Path, help="JDK 17 installation directory")
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--trials-per-aircraft", type=int, default=512,
                        help="Default 512 × 24 = 12288 trials")
    parser.add_argument("--ticks", type=int, default=180,
                        help="SOURCE updates per trial (20 Hz)")
    parser.add_argument("--trace-stride", type=int, default=10,
                        help="Time slice interval for 1 representative/scenario/aircraft")
    args = parser.parse_args()

    javac, java = get_java17(args.java_home)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="ww-flight-lab-java17-") as temp:
        classes = Path(temp) / "classes"
        compile_lab(javac, classes)
        compiled = time.perf_counter()
        summary = run_lab(java, classes, args.output, seed=args.seed,
                          trials_per_aircraft=args.trials_per_aircraft,
                          ticks=args.ticks, trace_stride=args.trace_stride)
        simulated = time.perf_counter()
    html = args.output / "flight-lab.html"
    make_html(args.output / "summary.json", args.output / "time_slices.csv", html)
    ended = time.perf_counter()
    print(f"FLIGHT_LAB_JDK17_REPORT PASS {summary['trial_count']} trials / "
          f"{summary['simulated_ticks']} SOURCE ticks")
    print(f"Timings: javac17={compiled-started:.3f}s "
          f"Java batch={simulated-compiled:.3f}s "
          f"HTML={ended-simulated:.3f}s total={ended-started:.3f}s")
    print("Files:", *(str(args.output / filename) for filename in
                       ("summary.json", "outcomes.csv", "time_slices.csv", "flight-lab.html")),
          sep="\n  ")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError, ValueError, RuntimeError) as exc:
        print(f"FLIGHT_LAB_FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

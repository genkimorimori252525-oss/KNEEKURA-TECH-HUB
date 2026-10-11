#!/usr/bin/env python3
"""One-command pinned-physics offline replay of ALL available real Forge evidence.

Compiles dependency-free original-IA physics Java 17 source; NEVER boots a
Minecraft process or loads proprietary game JARs. Preserves raw real input
unchanged and writes only generated CSV/JSON/HTML into the named output dir.

The 24 sequential 40-tick original-jar aircraft smoke receipts, five genuine
401-sample neutral acceleration receipts, and six longer combat/strike/RTB
controller receipts form the predeclared verification contract. If the
original GameTest artifacts are absent or adulterated, FAIL rather than
substituting a synthetic/source-only trace.
"""

from __future__ import annotations

import argparse
import csv
import locale
import os
from pathlib import Path
import subprocess
import sys

from physics_twin_review import WW_OWNER_SHA, verify

ROOT = Path(__file__).resolve().parent.parent
JAVA_PACKAGE = "org.kneekura.techhub.warfarewings.physics."
SOURCE_FILES = (
    "Ia133Microkernel.java", "PinnedIa133WindWorld.java", "WarfareWingsAircraft.java",
    "WarfareWingsEngineReaction.java", "AircraftAtlasMain.java", "TraceCsv.java",
    "RealPhysicsTwinReplayMain.java", "RealTacticalPhysicsTwinReplayMain.java",
)
NEUTRAL = ("a6m", "p47n", "spitfire", "il2", "b17")
LONG_TACTICAL = (
    ("op-red-1", "a6m"), ("op-blue-1", "p47n"),
    ("op-escort-left", "p47n"), ("op-b17", "b17"),
    ("operational-strike-il2", "il2"), ("operational-strike-b17", "b17"),
)


def expected_roster(anchor: Path) -> tuple[str, ...]:
    with anchor.open(encoding="utf-8", newline="") as handle:
        reader=csv.DictReader(handle)
        entries=list(reader)
    if len(entries)!=24 or len({e["aircraft_id"] for e in entries})!=24:
        raise ValueError("Exact pinned original 24-plane anchor is missing or duplicated")
    if any(e["anchor_sha256"]!=WW_OWNER_SHA or e["aircraft_id"]!="warfare_wings:"+e["base_id"]
           for e in entries):
        raise ValueError("Pinned owner JAR source roster hash was changed")
    return tuple(e["base_id"] for e in entries)


def _run(command: list[str]) -> None:
    # Windows JDK17 writes its console output in the configured CP932 locale;
    # decoding it as UTF-8 produces U+FFFD that PowerShell 5.1 cannot print.
    # Do not weaken the result/provenance gate to avoid a display error.
    result=subprocess.run(command, cwd=ROOT, capture_output=True,
                          encoding=locale.getpreferredencoding(False),errors="replace")
    if result.returncode:
        raise RuntimeError(f"Source Java17 verification failed: {' '.join(command[:5])}:\n"
                           + (result.stdout + result.stderr)[-4000:])
    if result.stdout.strip():
        print(result.stdout.strip(),flush=True)


def execute(anchor: Path, receipts: Path, output: Path, java_home: Path,
            max_final_drift: float=.01) -> dict:
    anchor=anchor.resolve()
    receipts=receipts.resolve()
    output=output.resolve()
    roster=expected_roster(anchor)
    required=([f"{name}-throttle-step-v1-runtime.csv" for name in NEUTRAL]
              + [f"roster-{name}-forge-controls.csv" for name in roster]
              + [f"{scenario}-forge-controls.csv" for scenario,_ in LONG_TACTICAL])
    missing=[name for name in required if not (receipts/name).is_file()]
    if missing:
        raise FileNotFoundError("Real original Forge required receipt absent: "+", ".join(missing))
    suffix=".exe" if os.name=="nt" else ""
    java=java_home/"bin"/("java"+suffix)
    javac=java_home/"bin"/("javac"+suffix)
    if not java.is_file() or not javac.is_file():
        raise ValueError("JAVA_HOME must point to installed Java 17 JDK with java and javac")
    version=subprocess.run([str(java),"-version"],capture_output=True,text=True,check=True)
    version_str=version.stderr+version.stdout
    if not ('version "17.' in version_str or 'version "17"' in version_str):
        raise ValueError("Exact offline source must run under Java 17")

    classes=output/"classes"
    traces=output/"paired"
    reports=output/"report"
    classes.mkdir(parents=True,exist_ok=True)
    traces.mkdir(parents=True,exist_ok=True)
    files=[str(ROOT/"src"/"main"/"java"/"org"/"kneekura"/"techhub"/"warfarewings"/"physics"/name)
           for name in SOURCE_FILES]
    _run([str(javac),"-encoding","UTF-8","--release","17","-d",str(classes),*files])
    common=[str(java),"-cp",str(classes)]
    for plane in NEUTRAL:
        _run([*common,JAVA_PACKAGE+"RealPhysicsTwinReplayMain",
              str(anchor),"warfare_wings:"+plane,str(receipts/f"{plane}-throttle-step-v1-runtime.csv"),
              str(traces/f"{plane}-pinned-wind.csv"),"--pinned-wind"])
    for scenario,plane in [*( ("roster-"+a,a) for a in roster ),*LONG_TACTICAL]:
        _run([*common,JAVA_PACKAGE+"RealTacticalPhysicsTwinReplayMain",
              str(anchor),"warfare_wings:"+plane,scenario,
              str(receipts/f"{scenario}-forge-controls.csv"),
              str(traces/f"{scenario}-pinned-wind.csv"),"--pinned-wind"])
    report=verify(traces,receipts,reports,expected_roster=24,expected_neutral=5,
                  expected_tactical=6,max_final_drift=max_final_drift)
    print("PHYSICS_TWIN_35_ORIGINAL_FORGE_REPLAYS",report["conclusion"],
          "airframes",report["real_aircraft"],"paired_ticks",report["paired_tick_samples"],
          "max_final_drift_blocks",report["maximum_free_run_final_position_error_blocks"],flush=True)
    if report["failed_gates"]:
        raise ValueError("Pinned original free-air physical replay failed: "+str(report["failed_gates"]))
    return report


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchor",type=Path,default=ROOT/"data/base-aircraft-anchor-v1.csv")
    parser.add_argument("--real-traces",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--java-home",type=Path,default=Path(os.environ.get("JAVA_HOME",".")))
    parser.add_argument("--max-final-drift",type=float,default=.01)
    args=parser.parse_args()
    try:
        execute(args.anchor,args.real_traces,args.output,args.java_home,args.max_final_drift)
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit("PINNED_PHYSICS_TWIN_FAILED: "+str(exc)) from None


if __name__=="__main__":
    main()

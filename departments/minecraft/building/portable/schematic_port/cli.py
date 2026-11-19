"""validate / convert: mcbuild build -> target-version Sponge schematic. No network, no world edits.

    python -m schematic_port inspect  <final.schem | sparse.json>
    python -m schematic_port validate <input> --target minecraft-java-1.20.1-forge
    python -m schematic_port convert  <input> --target minecraft-java-1.20.1-forge --out build.schem
    python -m schematic_port fetch-registry --target minecraft-java-1.20.1-forge   (explicit download)

Exit codes: 0 ok, 2 usage/input error, 3 blocked by target compatibility, 4 read-back diff.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import compat, ir as irmod, sponge_v2
from .blockstate import BlockStateError
from .nbt import NBTError
from .profile import ProfileError, load_profile

HUB_ROOT = Path(__file__).resolve().parents[5]
NOT_RUN = "NOT_RUN"


def load_input(path: Path, allow_dropping_extras: bool = False) -> irmod.BuildingIR:
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        return irmod.from_sponge_v3(data, allow_dropping_extras=allow_dropping_extras)
    return irmod.from_sparse_json(data)


def _origin(text: str | None) -> tuple[int, int, int] | None:
    if text is None:
        return None
    parts = text.split(",")
    if len(parts) != 3:
        raise ValueError("--origin must be x,y,z")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


def base_report(building: irmod.BuildingIR, profile, args) -> dict:
    b = building.bounds()
    return {
        "schema_version": 1,
        "kind": "kneekura_building_port_report",
        "source_kind": building.source.get("kind"),
        "source_commit": building.source.get("mcbuild_commit"),
        "source_sha256": building.source.get("sha256"),
        "source_data_version": building.source.get("data_version"),
        "source_content_sha256": building.content_sha256(),
        "air_intent": building.air_intent,
        "target_profile": profile.profile_id,
        "target": {"minecraft": profile.minecraft, "loader": profile.loader, "worldedit": profile.worldedit,
                   "schematic_version": profile.schematic_version, "data_version": profile.data_version},
        "block_count": len(building.solid),
        "explicit_air_count": len(building.explicit_air),
        "source_bounds": [list(b[0]), list(b[1])] if b else None,
        "paste_origin": list(building.paste_origin),
        "warnings": list(building.warnings),
        "substitutions": [],
        "air_policy": getattr(args, "air_policy", None),
        # Gates are reported separately and never merged (PLAN P4 / P5).
        "gates": {"P2_TARGET_COMPATIBILITY": NOT_RUN, "P3_FILE_READBACK": NOT_RUN,
                  "P4_READABLE_BY_WORLDEDIT": NOT_RUN, "P4_PASTE_IN_TEST_WORLD": NOT_RUN, "P4_VISUALLY_CHECKED": NOT_RUN},
        "validation_level": "NONE",
        "out_schem_sha256": None,
    }


def cmd_inspect(args) -> int:
    building = load_input(args.input, args.allow_dropping_extras)
    b = building.bounds()
    print(json.dumps({"source": building.source, "air_intent": building.air_intent, "block_count": len(building.solid),
                      "explicit_air_count": len(building.explicit_air), "bounds": b, "warnings": building.warnings,
                      "content_sha256": building.content_sha256(), **compat.summarize(building)}, indent=2, ensure_ascii=False))
    return 0


def _validate(args):
    profile = load_profile(args.target)
    registry = profile.registry(HUB_ROOT, args.registry)
    building = load_input(args.input, args.allow_dropping_extras)
    origin = _origin(args.origin)
    if origin is not None:
        building.paste_origin = origin
    table = compat.load_substitutions(args.substitutions.read_bytes(), registry) if args.substitutions else None
    result = compat.check(building, registry, table)
    report = base_report(building, profile, args)
    report["registry_sha256"] = registry.sha256
    report["substitutions"] = result.substitutions
    report["issues"] = result.issues
    report["partial_states_default_filled"] = result.partial_states
    report["gates"]["P2_TARGET_COMPATIBILITY"] = {"LOSSLESS": "PASS", "SUBSTITUTED": "PASS_WITH_EXPLICIT_SUBSTITUTIONS", "BLOCKED": "FAIL"}[result.status]
    report["compatibility"] = result.status
    report["validation_level"] = "TARGET_REGISTRY_CHECKED"
    return profile, registry, result, report


def cmd_validate(args) -> int:
    _, _, result, report = _validate(args)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 3 if result.status == "BLOCKED" else 0


def cmd_convert(args) -> int:
    if args.air_policy == sponge_v2.FULL_REPLACE and not args.confirm_full_replace:
        raise ValueError("full_region_replace overwrites terrain in the whole region; pass --confirm-full-replace to choose it")
    out: Path = args.out
    report_path = out.with_name(out.name + ".report.json")
    if out.exists() or report_path.exists():
        raise ValueError(f"refusing to overwrite {out} or its report")
    if out.resolve() == args.input.resolve():
        raise ValueError("output must not replace the source file")
    profile, registry, result, report = _validate(args)
    if result.status == "BLOCKED":
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("convert: blocked by target compatibility; nothing written", file=sys.stderr)
        return 3
    data, info = sponge_v2.write_v2(result.ir, profile, args.air_policy)
    readback = sponge_v2.read_v2(data)
    verdict = sponge_v2.verify_readback(result.ir, readback, profile, registry, args.air_policy)
    report["export"] = info
    report["warnings"] += info["warnings"]
    report["readback"] = verdict
    report["gates"]["P3_FILE_READBACK"] = "PASS" if verdict["status"] == "ZERO_DIFF" else "FAIL"
    if verdict["status"] != "ZERO_DIFF":
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("convert: read-back differs from the IR; nothing written", file=sys.stderr)
        return 4
    report["validation_level"] = "FILE_LEVEL_READBACK_ZERO_DIFF"
    report["out_schem_sha256"] = info["sha256"]
    report["paste_instructions"] = paste_instructions(args.air_policy)
    publish_exclusive(out, data)
    try:
        with open(report_path, "x", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
    except OSError:
        out.unlink()  # never leave an output without its report
        raise
    print(json.dumps({"out": str(out), "report": str(report_path), "sha256": info["sha256"],
                      "dimensions": info["dimensions"], "warnings": report["warnings"], "gates": report["gates"]}, indent=2))
    return 0


def publish_exclusive(out: Path, data: bytes) -> None:
    """Write to a unique temp file, then hard-link it into place: the link fails if `out` appeared
    meanwhile, so an existing file is never replaced and a reader never sees a partial file (review L6)."""
    fd, tmp = tempfile.mkstemp(prefix=out.name + ".", suffix=".tmp", dir=out.parent)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(tmp, out)
    finally:
        os.unlink(tmp)


def paste_instructions(air_policy: str) -> list[str]:
    steps = ["Use an isolated Forge 1.20.1 + WorldEdit 7.2.15 test world and back it up first.",
             "Copy the .schem into config/worldedit/schematics/, then `//schem load <name>`.",
             "Check the clipboard (`//schem list`, position preview) before pasting."]
    if air_policy == sponge_v2.SKIP_AIR:
        steps.append("Paste with `//paste -a` so air cells do not erase existing terrain.")
    else:
        steps.append("Plain `//paste` replaces EVERY cell in the region, including terrain, with the file's air.")
    return steps


def cmd_fetch_registry(args) -> int:
    from .registry_fetch import fetch
    profile = load_profile(args.target)
    out_dir = HUB_ROOT / Path(profile.registry_path).parents[2]
    result = fetch(profile.minecraft, out_dir, profile.registry_generator.get("server_sha1"))
    print(json.dumps(result, indent=2))
    if profile.registry_sha256 and result["blocks_sha256"] != profile.registry_sha256:
        print("fetch-registry: generated report differs from the pinned SHA-256", file=sys.stderr)
        return 4
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="schematic_port", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    def common(sp, target=True):
        sp.add_argument("input", type=Path, help="mcbuild final.schem (Sponge v3) or sparse JSON from export_sparse.py")
        sp.add_argument("--allow-dropping-extras", action="store_true", help="drop block entities/entities (not carried)")
        if target:
            sp.add_argument("--target", required=True)
            sp.add_argument("--registry", type=Path, help="registry override; must still match the profile pin")
            sp.add_argument("--substitutions", type=Path, help='explicit JSON table {"from": "to"}')
            sp.add_argument("--origin", help="paste origin x,y,z in design coordinates (default 0,0,0)")
    common(sub.add_parser("inspect", help="summarize an input; no target needed"), target=False)
    common(sub.add_parser("validate", help="check every block state against the target registry"))
    conv = sub.add_parser("convert", help="validate, write Sponge v2, read back, diff; write only on ZERO_DIFF")
    common(conv)
    conv.add_argument("--out", type=Path, required=True)
    conv.add_argument("--air-policy", choices=[sponge_v2.SKIP_AIR, sponge_v2.FULL_REPLACE], default=sponge_v2.SKIP_AIR)
    conv.add_argument("--confirm-full-replace", action="store_true")
    fr = sub.add_parser("fetch-registry", help="EXPLICIT network: generate the official blocks report locally")
    fr.add_argument("--target", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return {"inspect": cmd_inspect, "validate": cmd_validate, "convert": cmd_convert,
                "fetch-registry": cmd_fetch_registry}[args.cmd](args)
    except (OSError, ValueError, KeyError, RecursionError, RuntimeError, subprocess.SubprocessError,
            NBTError, BlockStateError, ProfileError, irmod.IRError, sponge_v2.ExportError) as exc:
        print(f"schematic_port: {exc}", file=sys.stderr)
        return 2

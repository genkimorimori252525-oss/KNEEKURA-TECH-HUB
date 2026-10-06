#!/usr/bin/env python3
"""
Static surface audit for the pinned QB-MOD / Garnet-MOD source trees.

This is a literal-text retrieval audit, not semantic analysis.
It intentionally does not fetch or redistribute source files.

Usage:
  python audit-static-surfaces.py \
    --qb /path/to/QB-MOD/MCP/puellamagi/mods \
    --garnet /path/to/Garnet-MOD/MCP/garnet/mods
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = {
    "todo": r"TODO",
    "stdout": r"System\.out\.(?:print|println)",
    "create_explosion": r"createExplosion\s*\(",
    "primed_tnt": r"EntityTNTPrimed",
    "set_health": r"\.setHealth\s*\(",
    "set_dead": r"\.setDead\s*\(",
    "set_block": r"\.setBlock(?:ToAir|AndMetadataWithUpdate)?\s*\(",
    "potion_effect": r"addPotionEffect\s*\(",
    "set_position": r"\.setPosition\s*\(",
    "entity_aabb_query": r"(?:get|select)EntitiesWithinAABB(?:ExcludingEntity)?",
    "nbt_write": r"writeEntityToNBT\s*\(",
    "nbt_read": r"readEntityFromNBT\s*\(",
    "legacy_custom_payload": r"Packet250CustomPayload",
    "data_watcher": r"dataWatcher",
    "lightning": r"(?:addWeatherEffect|EntityLightningBolt)",
    "firework": r"EntityFireworkRocket",
}

def scan_root(label: str, root: Path):
    files = sorted(root.rglob("*.java"))
    result = {key: {"occurrences": 0, "files": []} for key in PATTERNS}

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = f"{label}/{path.relative_to(root).as_posix()}"
        for key, pattern in PATTERNS.items():
            count = len(re.findall(pattern, text))
            if count:
                result[key]["occurrences"] += count
                result[key]["files"].append({"path": rel, "occurrences": count})

    return {"java_files": len(files), "patterns": result}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qb", type=Path, required=True)
    parser.add_argument("--garnet", type=Path, required=True)
    args = parser.parse_args()

    out = {
        "format": "kneekura.madomagi.static-surface-audit.v1",
        "note": "Literal-text retrieval inventory only; semantic interpretation belongs in analysis documents.",
        "roots": {
            "QB": scan_root("QB", args.qb),
            "Garnet": scan_root("Garnet", args.garnet),
        },
    }

    combined = {}
    for key in PATTERNS:
        combined[key] = {
            "occurrences": sum(out["roots"][name]["patterns"][key]["occurrences"] for name in ("QB", "Garnet")),
            "file_count": sum(len(out["roots"][name]["patterns"][key]["files"]) for name in ("QB", "Garnet")),
            "files": out["roots"]["QB"]["patterns"][key]["files"] + out["roots"]["Garnet"]["patterns"][key]["files"],
        }
    out["combined"] = combined
    out["java_files_total"] = out["roots"]["QB"]["java_files"] + out["roots"]["Garnet"]["java_files"]

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

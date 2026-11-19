"""Export mcbuild's sparse VoxelGrid (not the dense .schem) so air intent survives (PLAN P1).

Run it with mcbuild's own pinned environment; it imports mcbuild at runtime and copies no code:

    uv run --offline --frozen --no-sync python <this file> <blueprint.py> <out.json> [--seed N]

(working directory: the pinned mcbuild checkout). It executes the blueprint through mcbuild's
sandbox exactly as mcbuild does, then writes every cell VoxelGrid.items() holds: explicit
``air`` placements stay, cleared/unplaced cells are simply absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("blueprint", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    from mcbuild.dsl.sandbox import run_blueprint  # imported from the pinned checkout only
    from mcbuild.export.schem import DATA_VERSION
    from mcbuild.palette import get_block_by_index
    from mcbuild.voxel import VoxelGrid

    source = args.blueprint.read_text(encoding="utf-8")
    grid = VoxelGrid()
    run_blueprint(source, grid, seed=args.seed)
    cells = sorted([x, y, z, get_block_by_index(idx).mc_id] for (x, y, z), idx in grid.items())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip() or None
    doc = {"format": "kneekura_mcbuild_sparse_v1", "mcbuild_commit": commit,
           "blueprint_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(), "seed": args.seed,
           "data_version": DATA_VERSION, "cells": cells}
    if args.out.exists():
        print(f"refusing to overwrite {args.out}", file=sys.stderr)
        return 2
    args.out.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"cells": len(cells), "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

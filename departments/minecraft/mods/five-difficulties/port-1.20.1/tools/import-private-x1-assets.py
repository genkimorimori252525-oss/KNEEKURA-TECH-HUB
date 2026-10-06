#!/usr/bin/env python3
"""Import verified private X1 texture bytes into the local Forge resource tree.

The copied PNGs are gitignored. This script accepts either the original outer
5難題+アドオン達.zip or the canonical inner X1 ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import zipfile

OUTER_SHA = "9d8ea665ab8b925437fa2294f34051b8b9bdc6e9036c540f5c2a77432b689a98"
INNER_SHA = "6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634"

ASSETS = {
    "assets/thkaguyamod/textures/shot/HomingAmulet.png": (
        "assets/five_difficulties_port/textures/entity/homing_amulet.png",
        "badfeba690c2dee69ddb38c9f3a0fe538643ca1d439121e95959fd7dfb93b4d9",
    ),
    "assets/thkaguyamod/textures/items/homingAmulet.png": (
        "assets/five_difficulties_port/textures/item/homing_amulet.png",
        "650f71239534ef521bea3e1e29893ed1cb8302721854c44d0536b76be02f5773",
    ),
    "assets/thkaguyamod/textures/items/sakuyaWatch.png": (
        "assets/five_difficulties_port/textures/item/sakuya_watch.png",
        "589e080353f2f1d56ec6af6547bc3cfbb3802de89e7797c03a2251083e8d0c8e",
    ),
    "assets/thkaguyamod/textures/SakuyaWatchTexture.png": (
        "assets/five_difficulties_port/textures/entity/sakuya_watch.png",
        "b55d8af1138f2b7f5e3841afe7d5aecff78d57122f57ecb7a29af1036f76ff30",
    ),
    "assets/thkaguyamod/textures/items/SakuyaStopWatch.png": (
        "assets/five_difficulties_port/textures/item/sakuya_stopwatch.png",
        "ac6144bc483951782cbcf94cdc3339f07fbc1f49507a323264ee27a5f922e285",
    ),
    "assets/thkaguyamod/textures/SakuyaStopWatchTexture.png": (
        "assets/five_difficulties_port/textures/entity/sakuya_stopwatch.png",
        "9c6b567304210c30b67d14dc925d058dc3eb5c961aae8918aee84bb7239955bd",
    ),
    "assets/thkaguyamod/textures/DarkTexture.png": (
        "assets/five_difficulties_port/textures/entity/sakuya_time_dark.png",
        "c0b1a2f92f0b3f366cdfcecf212de161eb853fd987d2790bd7d943b4dcde0d05",
    ),
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_inner(raw: bytes) -> bytes:
    digest = sha(raw)
    if digest == INNER_SHA:
        return raw
    if digest != OUTER_SHA:
        raise SystemExit(f"input SHA-256 {digest} is neither canonical outer nor inner X1")

    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        for name in outer.namelist():
            candidate = outer.read(name)
            if sha(candidate) == INNER_SHA:
                return candidate
    raise SystemExit("canonical X1 inner archive not found in verified outer bundle")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument(
        "--resources",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src" / "main" / "resources",
    )
    args = ap.parse_args()

    inner = canonical_inner(args.archive.read_bytes())
    with zipfile.ZipFile(io.BytesIO(inner)) as zf:
        for source, (destination, expected) in ASSETS.items():
            data = zf.read(source)
            actual = sha(data)
            if actual != expected:
                raise SystemExit(f"{source}: SHA mismatch {actual} != {expected}")
            out = args.resources / destination
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"IMPORTED {source} -> {out} sha256={actual}")

if __name__ == "__main__":
    main()

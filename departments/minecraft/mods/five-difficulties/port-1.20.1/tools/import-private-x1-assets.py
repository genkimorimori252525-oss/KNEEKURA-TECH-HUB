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
    # P8 generic THShot: RenderTHShot sprite strips (8 colour columns) and the delay light.
    "assets/thkaguyamod/textures/shot/SmallShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/small_shot.png",
        "a1fae537d35016dd43cd5af3058616a833ed2c157ac603f37899b1dd0e6b943f",
    ),
    "assets/thkaguyamod/textures/shot/PearlShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/pearl_shot.png",
        "d06dd8b8751bba385c17e9c620b4723327389913a95dcf19fc2b26b6b9530576",
    ),
    "assets/thkaguyamod/textures/shot/CircleShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/circle_shot.png",
        "817b2de8514f8a7116f782337775550211986f790cb38e1cc9c69ac0b7b26359",
    ),
    "assets/thkaguyamod/textures/shot/HeartShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/heart_shot.png",
        "7d2927c4b8c3311d326719faab41b94efc0ea3001699d918f67b60c1b4b614d6",
    ),
    "assets/thkaguyamod/textures/shot/BigShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/big_shot.png",
        "59bb9c4df6907b19805322e4c0d62264a25fdd2c8d924022892b2c0fb0a1dd31",
    ),
    "assets/thkaguyamod/textures/shot/MusouFuuin.png": (
        "assets/five_difficulties_port/textures/entity/shot/musou_fuuin.png",
        "1fe5340a695754e4ae73c52c2d91638f775a2a08aba107da52b35916cf75e438",
    ),
    # P8 ItemTHShot two-pass icons (layer0 tinted by NBT Color, layer1 white).
    "assets/thkaguyamod/textures/items/shot/SmallShot.png": (
        "assets/five_difficulties_port/textures/item/shot/small_shot.png",
        "f118752099d7b77c48b99494eeae50993bbb9a64fe9a08027a5bd9c3a38634ed",
    ),
    "assets/thkaguyamod/textures/items/shot/SmallShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/small_shot_2.png",
        "d329d9089f1c7155bc762b9d39b8ef517df6f42622144fa91a8821bdf221f7c0",
    ),
    "assets/thkaguyamod/textures/items/shot/TinyShot.png": (
        "assets/five_difficulties_port/textures/item/shot/tiny_shot.png",
        "f3073625d3760f733dd6c48e90499a358b3d916ac128f2c400c101d9c2857b5d",
    ),
    "assets/thkaguyamod/textures/items/shot/TinyShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/tiny_shot_2.png",
        "24a0c0152810c685579b201adef54875d7741660feab24180abc4429fabb11bd",
    ),
    "assets/thkaguyamod/textures/items/shot/MediumShot.png": (
        "assets/five_difficulties_port/textures/item/shot/medium_shot.png",
        "b9ec16cfc0a05b1e2fe9ee0a6a007258bd02098b381401b53ae1a3c4fb9f5912",
    ),
    "assets/thkaguyamod/textures/items/shot/MediumShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/medium_shot_2.png",
        "aded0d55152b45296c26fc5f8a21d2be17229fde53af757a9966564044a6ed9f",
    ),
    "assets/thkaguyamod/textures/items/shot/BigShot.png": (
        "assets/five_difficulties_port/textures/item/shot/big_shot.png",
        "0adac9ea5226cfead7ff74b23b142a4e971a1c4ce8a498bd0ff25076bd1d3beb",
    ),
    "assets/thkaguyamod/textures/items/shot/BigShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/big_shot_2.png",
        "10a1cec8f27a512b5a5eb1e881e2b41f82259c281d7c36357d3c3a72e929ef7f",
    ),
    "assets/thkaguyamod/textures/items/shot/CircleShot.png": (
        "assets/five_difficulties_port/textures/item/shot/circle_shot.png",
        "62b3f926573f8e2ae3a02ae3af71084870f575278ed46a0cfba6cc9bbf79607a",
    ),
    "assets/thkaguyamod/textures/items/shot/CircleShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/circle_shot_2.png",
        "7545d906c9101d2818726700c2715eb70de1f0dcb05d41ab750478b7dc944b34",
    ),
    "assets/thkaguyamod/textures/items/shot/HeartShot.png": (
        "assets/five_difficulties_port/textures/item/shot/heart_shot.png",
        "347fe203ee3426ee67291e952737d948d9597da62cef1680557d632955afb41c",
    ),
    "assets/thkaguyamod/textures/items/shot/HeartShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/heart_shot_2.png",
        "f2efcd8af85341e3d9c9524b82b039f4424e6c29ffcb60fc4e2041c4443035ef",
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

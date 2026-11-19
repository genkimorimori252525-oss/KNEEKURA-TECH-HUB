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
    "assets/thkaguyamod/textures/items/diffusionAmulet.png": (
        "assets/five_difficulties_port/textures/item/diffusion_amulet.png",
        "48a04fbb8993b87cce4abc2b175f006d8bdaef3254c323b86b023b749f152927",
    ),
    # P9 remaining shot forms, silver knives, familiar and the remaining ItemTHShot icons.
    "assets/thkaguyamod/textures/items/shot/StarShot.png": (
        "assets/five_difficulties_port/textures/item/shot/star_shot.png",
        "a30c378badbf2b8c14205005f8db8d50b61530b22c02cd31588af5638d87c9e8",
    ),
    "assets/thkaguyamod/textures/items/shot/StarShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/star_shot_2.png",
        "0c6f9f867c37aee844e08718b0b8e50cc28ae15352d01a0674ba1c0b518fa89c",
    ),
    "assets/thkaguyamod/textures/items/shot/SmallStarShot.png": (
        "assets/five_difficulties_port/textures/item/shot/small_star_shot.png",
        "54e69818a777d6e1654894153169072402e5e4956bec967d7fe4bf6a3fbb5a3c",
    ),
    "assets/thkaguyamod/textures/items/shot/SmallStarShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/small_star_shot_2.png",
        "59be1aec16255efdc0ca9148aa6738e2009e1610dac5d36f2b10e6d569a3d9fb",
    ),
    "assets/thkaguyamod/textures/items/shot/ScaleShot.png": (
        "assets/five_difficulties_port/textures/item/shot/scale_shot.png",
        "c77300df5822b0ca4caea8199e355cea5e7631963acf13f8b537796d2c5ebad2",
    ),
    "assets/thkaguyamod/textures/items/shot/ScaleShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/scale_shot_2.png",
        "e47ecae4a0ba13a6c05f1c5d1bdf8226ba6fd50dd5f9b2a13b4bc6d6d6109043",
    ),
    "assets/thkaguyamod/textures/items/shot/ButterflyShot.png": (
        "assets/five_difficulties_port/textures/item/shot/butterfly_shot.png",
        "a85db4c120ee1830d3b602168a031f9ee605e22bd26f9c2df669ce26e387b48f",
    ),
    "assets/thkaguyamod/textures/items/shot/ButterflyShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/butterfly_shot_2.png",
        "0af198a54d314d67c0de4934d7d9b31ef9c0395c93fff611b6f9ae1523d36c7c",
    ),
    "assets/thkaguyamod/textures/items/shot/LightShot.png": (
        "assets/five_difficulties_port/textures/item/shot/light_shot.png",
        "70788947c65fbca3fcc3e6b9ca760541b491ce012baa591a62d645a2ea9ee208",
    ),
    "assets/thkaguyamod/textures/items/shot/LightShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/light_shot_2.png",
        "d6f76b048ed9d1e98c0f68c8980e0a79b4d7a362f8cf5f5147334d1eecb16bfa",
    ),
    "assets/thkaguyamod/textures/items/shot/KnifeShot.png": (
        "assets/five_difficulties_port/textures/item/shot/knife_shot.png",
        "537c13227e80a87a49efb88456de6aead1ab43af363d06e5f1832b62503e85f8",
    ),
    "assets/thkaguyamod/textures/items/shot/KnifeShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/knife_shot_2.png",
        "ce6a4e77908b0eefaeaa6746f1a404383fa6898ba1c0c16e838b5bc46256ed80",
    ),
    "assets/thkaguyamod/textures/items/shot/KunaiShot.png": (
        "assets/five_difficulties_port/textures/item/shot/kunai_shot.png",
        "88f201f1617cf90469d395ed199703c06b1f07a705147f3f72cea8aa226d2cd3",
    ),
    "assets/thkaguyamod/textures/items/shot/KunaiShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/kunai_shot_2.png",
        "3e5ce25f99b57235847fbbb0ba847ab2f868f2b4d511bd92b1fe5cacafaf2d8a",
    ),
    "assets/thkaguyamod/textures/items/shot/TalismanShot.png": (
        "assets/five_difficulties_port/textures/item/shot/talisman_shot.png",
        "81b6a1cd0c74f5f49a4097680e72b9913a20d013a0cc06e74ca3b0e9db389fe6",
    ),
    "assets/thkaguyamod/textures/items/shot/TalismanShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/talisman_shot_2.png",
        "3e71de3692440aaeeb9dba062bb0c95d849f82913791832cbd61f1c94b44d623",
    ),
    "assets/thkaguyamod/textures/items/shot/BigLightShot.png": (
        "assets/five_difficulties_port/textures/item/shot/big_light_shot.png",
        "86c176875955d354923a75e1ea57f5c3a8d233aa309ac86b8b6ccecc4c23e831",
    ),
    "assets/thkaguyamod/textures/items/shot/BigLightShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/big_light_shot_2.png",
        "199e2f39d2e4a2bf755a5e203a7f74b40b79ef189105d836c1255c047a9dc3c4",
    ),
    "assets/thkaguyamod/textures/items/shot/RiceShot.png": (
        "assets/five_difficulties_port/textures/item/shot/rice_shot.png",
        "bf04ceae28e1b8659313baf7d937fdddead4413011b57b5dccaa021a51822143",
    ),
    "assets/thkaguyamod/textures/items/shot/RiceShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/rice_shot_2.png",
        "b0296b18ddfd74c986c07714207481e9dc1f3e6209380f69baccce6a87f6480b",
    ),
    "assets/thkaguyamod/textures/items/shot/OvalShot.png": (
        "assets/five_difficulties_port/textures/item/shot/oval_shot.png",
        "3b993a8f7d1cb6eb777d6d52ea529cc6e854adb1785167e8b7d083f3fb866167",
    ),
    "assets/thkaguyamod/textures/items/shot/OvalShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/oval_shot_2.png",
        "722457c5c76adebc3073c07a8e7822f1d0110e2715d1d48c146bccf264e6051b",
    ),
    "assets/thkaguyamod/textures/items/shot/CrystalShot.png": (
        "assets/five_difficulties_port/textures/item/shot/crystal_shot.png",
        "a48941330112dacc5cebe0e1bbc8e972f69c7dcb1be2693dbe266da5ac7189a2",
    ),
    "assets/thkaguyamod/textures/items/shot/CrystalShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/crystal_shot_2.png",
        "9359de893d586d498f07fca65a5dd33665c37d86c7c55940c417315e9de7a38f",
    ),
    "assets/thkaguyamod/textures/items/shot/ArrowShot.png": (
        "assets/five_difficulties_port/textures/item/shot/arrow_shot.png",
        "ddcb9f6aa61cdd2ea23a043573fdd65c57ecf3ea15379b2b7a7c3af9925b46ce",
    ),
    "assets/thkaguyamod/textures/items/shot/ArrowShot_2.png": (
        "assets/five_difficulties_port/textures/item/shot/arrow_shot_2.png",
        "ebd88497ce90916401474953dfa6cd479bf8ef7f27e8a120f3984fa829bd4e36",
    ),
    "assets/thkaguyamod/textures/shot/StarShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/star_shot.png",
        "4c34a8041cf508bc9937e9e14de04e1d8d186170309865d023b9639b144379f5",
    ),
    "assets/thkaguyamod/textures/shot/ButterflyShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/butterfly_shot.png",
        "fa0e411fe29844cbeedc8f6675b1895700156952d48dd195ff7ba1b71f2e29b7",
    ),
    "assets/thkaguyamod/textures/shot/Laser.png": (
        "assets/five_difficulties_port/textures/entity/shot/laser.png",
        "4173f5d7613c88027d45148bc2e2f473aeb0f6a8cc97b88512063fc1516bae4a",
    ),
    "assets/thkaguyamod/textures/shot/KunaiShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/kunai_shot.png",
        "52713fd1930b4cb243e7c3d0bbf78e1f19f940647441b0846232864c4e9a7178",
    ),
    "assets/thkaguyamod/textures/shot/ArrowShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/arrow_shot.png",
        "bfd964b6f5b404cc8e938da40bee2e924b021623bb2a9714b84f50cb307b396c",
    ),
    "assets/thkaguyamod/textures/shot/TalismanShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/talisman_shot.png",
        "0c44e6554ec6813d539d91e6d4edf920ef37d3d4140f2b615b15e6188b2179bb",
    ),
    "assets/thkaguyamod/textures/shot/WindShot.png": (
        "assets/five_difficulties_port/textures/entity/shot/wind_shot.png",
        "ce352673ada9f49056c9eda1c9b89f1a4f69f325c761aaf16f0e6c51bdb3c805",
    ),
    "assets/thkaguyamod/textures/shot/DiffusionAmulet.png": (
        "assets/five_difficulties_port/textures/entity/shot/diffusion_amulet.png",
        "e73ca263f48df41e29712920c398145385d3b0226ccf706531f10e0e15d04213",
    ),
    "assets/thkaguyamod/textures/mob/Familiar.png": (
        "assets/five_difficulties_port/textures/entity/shot/familiar.png",
        "e2257429fa7999bba3727d131550dae5266c0b628c75c907da209a9814c125ea",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Red.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_red.png",
        "76b9992e9d08946e181b9b17be21bbece8a9406b9e296cda34aa4ec7c55d489a",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Blue.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_blue.png",
        "e888a7df0507111eb26c2ed9c0b2f6c4a18ac198fd04c6d5f6c7ec8caae5491c",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Green.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_green.png",
        "1405063927b75f5c38f3867833bd02095c575aec9ff153753c9ac22b3e0be20c",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Yellow.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_yellow.png",
        "ed5b4b630316aeffa8aad20c6c967f851067f9e501f597275007baf9edbc849d",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Purple.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_purple.png",
        "2cabfccb34052aa69c7fb0f244c760c6178828514dd49bf65445c78ea954c38f",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Aqua.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_aqua.png",
        "20a480fa805ffbf2464df499a78f3793f6c7f32082f429d06d51e2c3a8fa18d0",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_Orange.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_orange.png",
        "d1133f36ccac61f9eaf15614edb07aceac90ae00c6eeb7cabc07fd7e497425cd",
    ),
    "assets/thkaguyamod/textures/shot/SilverKnife_White.png": (
        "assets/five_difficulties_port/textures/entity/shot/silver_knife_white.png",
        "8da12ca6ee191c544aa8407cdccf38aff65d656b78c616f1bf1d860b6f4d5f71",
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

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
    # P16a small items.
    "assets/thkaguyamod/textures/items/heavenlyPeach.png": (
        "assets/five_difficulties_port/textures/item/heavenly_peach.png",
        "4c7fa9e18880a95258bb6a3e0da846ba2ca6a6e2be5f3f42ef0a4bcf3c0bce5c",
    ),
    "assets/thkaguyamod/textures/items/koyasugai.png": (
        "assets/five_difficulties_port/textures/item/swallow_cowrie_shell.png",
        "5f751d184d32d75a648e56d7de40cdb39538c39aa2e95838e68c1cfde67f0aa7",
    ),
    "assets/thkaguyamod/textures/items/closedThirdEye.png": (
        "assets/five_difficulties_port/textures/item/closed_third_eye.png",
        "9e81f4b78f2d60ca58bc4eff1c7403a56b83146b60f57c395a8bc3025d9d63df",
    ),
    "assets/thkaguyamod/textures/items/tenguFan.png": (
        "assets/five_difficulties_port/textures/item/tengu_fan.png",
        "5376ea52f20b5d88ffb8dc34452ab7d8844c1be80f25fcaaa0902333dd3b1f61",
    ),
    "assets/thkaguyamod/textures/items/onbashira.png": (
        "assets/five_difficulties_port/textures/item/onbashira.png",
        "d940dccf576a4f86ac0178da31cc5bffc56c64c4106501e911200fc70a7da8f2",
    ),
    "assets/thkaguyamod/textures/items/material/RedPearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_red.png",
        "989ee845785df5a24f74ae7558fa4dffd6924af77999d36895dac99739ded612",
    ),
    "assets/thkaguyamod/textures/items/material/BluePearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_blue.png",
        "9aade49bd42ba4b2320bd9bef98571e77e67fe46333ce82f0c502022a94b8518",
    ),
    "assets/thkaguyamod/textures/items/material/GreenPearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_green.png",
        "0bc46fef976cd41e8183adca4a9053aeae5d8e720c3150dc9cee3491d7838222",
    ),
    "assets/thkaguyamod/textures/items/material/YellowPearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_yellow.png",
        "eb07848f0faf2a8ef770552aa54877d839149f2995786f174b04b71934c1e6b0",
    ),
    "assets/thkaguyamod/textures/items/material/PurplePearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_purple.png",
        "6bfd40ea8b320e72d835a582df1baa3b1451e4283f5f75f5814d50a69707067c",
    ),
    "assets/thkaguyamod/textures/items/material/AquaPearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_aqua.png",
        "b0d46f4cb1b0caa0c036c9c637c0a35cdd1da85a6d4910508a29858dccdd22f7",
    ),
    "assets/thkaguyamod/textures/items/material/OrangePearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_orange.png",
        "f736c6a929c49e6a2b26d5c10f45527784f8877f95e714f5e0afa92b64e9e082",
    ),
    "assets/thkaguyamod/textures/items/material/WhitePearl.png": (
        "assets/five_difficulties_port/textures/item/hourai_pearl_white.png",
        "300952f4eb801945bfd493f6961685ae694350664bfb657ecbb9663c74dde4dc",
    ),
    # P16b weapons.
    "assets/thkaguyamod/textures/items/Gungnir.png": (
        "assets/five_difficulties_port/textures/item/spear_the_gungnir.png",
        "530312c7407ca56e85ad4d7cacc00bc95885a6ef7073e17ada89c2dbf02fff4f",
    ),
    "assets/thkaguyamod/textures/items/Laevateinn.png": (
        "assets/five_difficulties_port/textures/item/laevateinn.png",
        "d2c719e06b27cfb72b77d6f35e6aa2544c94b342fc7e3ddcfa24d483d8d7cdfa",
    ),
    "assets/thkaguyamod/textures/items/roukanSword.png": (
        "assets/five_difficulties_port/textures/item/roukanken.png",
        "1f62aaa294a9a73cc54858c226a67a1fbc3ca6dd62386767f235f803ecd10c3a",
    ),
    "assets/thkaguyamod/textures/items/roukanSword.png": (
        "assets/five_difficulties_port/textures/item/roukanken_senpuuzin.png",
        "1f62aaa294a9a73cc54858c226a67a1fbc3ca6dd62386767f235f803ecd10c3a",
    ),
    "assets/thkaguyamod/textures/items/deathScythe.png": (
        "assets/five_difficulties_port/textures/item/death_scythe.png",
        "6edced0174438767a5f4b26eefc346cb7d8a3efe990f3388d59093ada588e837",
    ),
    "assets/thkaguyamod/textures/items/kaigoStick_0.png": (
        "assets/five_difficulties_port/textures/item/remorse_rod.png",
        "353c459c5581b5b6a069d51e690b3007e09de679293645469ba895d346f49226",
    ),
    # P16b remorse rod, used.
    "assets/thkaguyamod/textures/items/kaigoStick_1.png": (
        "assets/five_difficulties_port/textures/item/remorse_rod_used.png",
        "48c28972ea3b5299e70cc71284aa6958222e19e28b3fdc20ebc8ca73b5efad06",
    ),
    # P16c shot items.
    "assets/thkaguyamod/textures/items/soulTorch.png": (
        "assets/five_difficulties_port/textures/item/soul_torch.png",
        "58aab3c885f789bcacc925fdcfc25f0bc07f09b34331e9be3ebdf325555f0deb",
    ),
    "assets/thkaguyamod/textures/items/yuyukoOugi.png": (
        "assets/five_difficulties_port/textures/item/yuyuko_fan.png",
        "a7bc9e85ab92814f4b6f9c8e80b26a3c9ebaff641f10e7f7da6b1fa2410dc4f6",
    ),
    "assets/thkaguyamod/textures/items/kappaWaterPistol.png": (
        "assets/five_difficulties_port/textures/item/kappa_water_pistol.png",
        "8676e022d5d4d468553dcbe756fb0832b5b18b3c9ad3a9f97bd949ad53762c47",
    ),
    "assets/thkaguyamod/textures/items/ibukihyou.png": (
        "assets/five_difficulties_port/textures/item/ibuki_gourd.png",
        "c7a6ec9a91c22f0b9ce7341486540a3a6a91011faac0d1b4426486abf4fd4e2d",
    ),
    # P16d entity textures.
    "assets/thkaguyamod/textures/SpiritualStrikeTalismanTexture.png": (
        "assets/five_difficulties_port/textures/entity/spiritual_strike_talisman.png",
        "387f00ef269ad865829386692743959d2c53cdc837f5b9f0d8c0e9718cd2a847",
    ),
    "assets/thkaguyamod/textures/Mazinkyoukan_Texture.png": (
        "assets/five_difficulties_port/textures/entity/mazinkyoukan.png",
        "804aea986d71abd58831b59574f7ea913525834d5364274d506f07272c225875",
    ),
    # P16d effect items.
    "assets/thkaguyamod/textures/items/SpiritualStrikeTalisman.png": (
        "assets/five_difficulties_port/textures/item/spiritual_strike_talisman.png",
        "ed85e00d4fa50bb412e80ed839a08a0cceabce059eca7c21f5d988b1c13b16af",
    ),
    "assets/thkaguyamod/textures/items/mazinKyoukan.png": (
        "assets/five_difficulties_port/textures/item/sorcerer_sutra_scroll.png",
        "251e8e9b05e6acc02f22d465bcdad4f0ee284d53cb07188b0af1ccb7ff2f1c3b",
    ),
    # P15 danmaku crafting table.
    "assets/thkaguyamod/textures/blocks/danmaku_crafting_table.png": (
        "assets/five_difficulties_port/textures/block/danmaku_crafting_table.png",
        "42f6fce6bbf10d50405fb384474ad872fb56f5e9ae118de343dbd2a16ec26306",
    ),
    "assets/thkaguyamod/textures/blocks/danmaku_crafting_table2.png": (
        "assets/five_difficulties_port/textures/block/laser_crafting_table.png",
        "e123460b05e7be9165a66647b56accee03897588a6af25f32dd27b4e5f5b6307",
    ),
    "assets/thkaguyamod/textures/gui/danmaku_crafting_table.png": (
        "assets/five_difficulties_port/textures/gui/danmaku_crafting_table.png",
        "4324a683864bfb8644a377639ccc622192671dc3cfdf5aaa072838dd147fb2a3",
    ),
    "assets/thkaguyamod/textures/gui/laser_crafting_table.png": (
        "assets/five_difficulties_port/textures/gui/laser_crafting_table.png",
        "1abbcf6dc80a4ac12f90962000c468046c80670b44f94744a6507928eced00ba",
    ),
    # P14 bonus items.
    "assets/thkaguyamod/textures/items/material/SmallPowerUpItem.png": (
        "assets/five_difficulties_port/textures/item/power_item_small.png",
        "7fd29895d4937c6d1e19cac2f6afd8fd896c6eb4e71b839bfcd44d1926ec4b40",
    ),
    "assets/thkaguyamod/textures/items/material/BigPowerUpItem.png": (
        "assets/five_difficulties_port/textures/item/power_item_big.png",
        "572feea020916ccff0813cb1a7de01dc51fb588825bca3c4cdca6b70a73f1c7f",
    ),
    "assets/thkaguyamod/textures/items/material/THPointItem.png": (
        "assets/five_difficulties_port/textures/item/point_item.png",
        "95aaed45f5dc492adb57f60e9d1e5d762622a93db0c693b38600bb67411978c4",
    ),
    "assets/thkaguyamod/textures/items/material/BombItem.png": (
        "assets/five_difficulties_port/textures/item/bomb_item.png",
        "10c8f0bf4268dca5437b0ee897c97a0be5522a081c71e15cebea3a17fc641d6d",
    ),
    "assets/thkaguyamod/textures/items/material/ExtendItem.png": (
        "assets/five_difficulties_port/textures/item/extend_item.png",
        "3c43ae112781819913d840ea5aac250daa83cf3df9e1223e968e234501a293c8",
    ),
    # P13d gaps.
    "assets/thkaguyamod/textures/items/sukima.png": (
        "assets/five_difficulties_port/textures/item/gap.png",
        "2da2286b8fae92b25c3fc7b4faaa4c45bd3073853cdb1cd2ef73d1a1cd180ba3",
    ),
    "assets/thkaguyamod/textures/items/GapFoldingUmbrella_base.png": (
        "assets/five_difficulties_port/textures/item/gap_folding_umbrella_base.png",
        "e245f3b395ca533d8e695eda274adf39c54475d9538eab7467e436ff3e5593bd",
    ),
    "assets/thkaguyamod/textures/items/GapFoldingUmbrella_ribbon.png": (
        "assets/five_difficulties_port/textures/item/gap_folding_umbrella_ribbon.png",
        "7d377c9aa7c25abc2a7b9e70a0baba794b7e3f73c3038ed1288c9774edf276bb",
    ),
    # P13c wind gohei.
    "assets/thkaguyamod/textures/items/mikoStick_S.png": (
        "assets/five_difficulties_port/textures/item/wind_miko_stick.png",
        "14c13c1bc39f532a843073d6df52ca9d6ef3de2625c19c70408dce7a65709523",
    ),
    "assets/thkaguyamod/textures/MiracleCircle.png": (
        "assets/five_difficulties_port/textures/entity/miracle_circle.png",
        "b934f402b23211aa5aeef96f2c6f30e2a49917d121670841b77bc5285437cc0d",
    ),
    # P13b gohei and Yin-Yang Orb.
    "assets/thkaguyamod/textures/items/HakureiOharaibou.png": (
        "assets/five_difficulties_port/textures/item/hakurei_miko_stick.png",
        "1f44155965c25208532b5e0f3fa56a6f2d2287ceb07088139542cf5f2188daf2",
    ),
    "assets/thkaguyamod/textures/shot/Onmyoudama2.png": (
        "assets/five_difficulties_port/textures/entity/shot/onmyoudama.png",
        "00698744f4f2040fa43c6d7663795072dc7f5fa750fe84665fc2856ace7d7c70",
    ),
    # P13 danmaku-weapon items.
    "assets/thkaguyamod/textures/items/miniHakkero.png": (
        "assets/five_difficulties_port/textures/item/mini_hakkero.png",
        "cf27ebc5dd106563f4a416cb0b37836a5cc06c6f58c41fc1c2941494396a50fe",
    ),
    "assets/thkaguyamod/textures/items/nuclearControlRod.png": (
        "assets/five_difficulties_port/textures/item/nuclear_control_rod.png",
        "51dc100b50441de90c772785ab3ee0e8d0a86d5db3c07078e8c0190cd0abf5b6",
    ),
    "assets/thkaguyamod/textures/items/ryuuTama.png": (
        "assets/five_difficulties_port/textures/item/dragon_neck_jewel.png",
        "bf918d4f10ab28af5230bb61d5cc8ad7a10d57f70fde9e0daaa390c0738b7f3d",
    ),
    "assets/thkaguyamod/textures/thKaguyaTerrain.png": (
        "assets/five_difficulties_port/textures/entity/th_kaguya_terrain.png",
        "2fef9748d6ca4cd2631df44b7f78cfbda3fea382e730658ec3b51a9ed7524d3f",
    ),
    # P12 spell-card entities.
    "assets/thkaguyamod/textures/MiniHakkeroTexture.png": (
        "assets/five_difficulties_port/textures/entity/mini_hakkero.png",
        "c03e896d0fc97bfdbae474fe0fe5ade90a365bce5271163403924b5b831acb7b",
    ),
    "assets/thkaguyamod/textures/SukimaTexture3.png": (
        "assets/five_difficulties_port/textures/entity/sukima.png",
        "8f28ca100736a557eac20b163d48ba14c9b148d1585aeb2d5043679d25959e2a",
    ),
    # P11 spell card art, level frames and the shot material.
    "assets/thkaguyamod/textures/items/spellCard/Catadioptric.png": (
        "assets/five_difficulties_port/textures/item/spellcard/catadioptric.png",
        "faae4e35ae7571582c556ed4cd2997fa79baf7e8f68efa1d94aadb1abf6a704e",
    ),
    "assets/thkaguyamod/textures/items/spellCard/EternalMeek.png": (
        "assets/five_difficulties_port/textures/item/spellcard/eternalmeek.png",
        "15b842e0458265711ad29d5511083d4bccfe49cc782e04f10e5ed8a6fbb6c72a",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Fafrotskies_no_Kiseki.png": (
        "assets/five_difficulties_port/textures/item/spellcard/fafrotskies_no_kiseki.png",
        "a8e16e24f35ab5ace9310cb248e9ad66a437fbcc2613b28176d9a3aa935ab37b",
    ),
    "assets/thkaguyamod/textures/items/spellCard/FujiyamaVolcano.png": (
        "assets/five_difficulties_port/textures/item/spellcard/fujiyamavolcano.png",
        "b95f5a9ab6979afcf2b9311700ca922a17c3b7c59a7c78b5f6e9454c5f34447b",
    ),
    "assets/thkaguyamod/textures/items/spellCard/GagoujiCyclone.png": (
        "assets/five_difficulties_port/textures/item/spellcard/gagoujicyclone.png",
        "bca6b96c6d854e90eb86c5a80597f1869419efae46858a410b548ce7cb86102d",
    ),
    "assets/thkaguyamod/textures/items/spellCard/HikouchuuNest.png": (
        "assets/five_difficulties_port/textures/item/spellcard/hikouchuunest.png",
        "709d8970f730d134f6d431837729ca61225b6d0ed8276fdcf38a246bdc13dccc",
    ),
    "assets/thkaguyamod/textures/items/spellCard/HoukaKenran.png": (
        "assets/five_difficulties_port/textures/item/spellcard/houkakenran.png",
        "c9863ee00872d70c4fce5b671c48c06f220fe63e6b6da760eedffcee113bf6c6",
    ),
    "assets/thkaguyamod/textures/items/spellCard/IcicleFall.png": (
        "assets/five_difficulties_port/textures/item/spellcard/iciclefall.png",
        "f23179e42278eb5fec7db2b519f49282731005047a485d3168dba633f741d52f",
    ),
    "assets/thkaguyamod/textures/items/spellCard/KachoufuugetuShoufuurougetu.png": (
        "assets/five_difficulties_port/textures/item/spellcard/kachoufuugetushoufuurougetu.png",
        "ca35a65d8078f55dbaadfd1c7978c41b8ef799be394632e14eea2f53977c040d",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Kappa'sPororoca.png": (
        "assets/five_difficulties_port/textures/item/spellcard/kappaspororoca.png",
        "026167a275ac9b8909f3b94e77614eb3e0e756bfde5ccd76a92ac512cd067f3a",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Kasho_no_Eimin.png": (
        "assets/five_difficulties_port/textures/item/spellcard/kasho_no_eimin.png",
        "033e8856b6f2f4a7a69c1c32f07a9d3a9fd4fa1c442ecf341154747baf9c9efc",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Kerochan_Fuuu_ni_Makezu.png": (
        "assets/five_difficulties_port/textures/item/spellcard/kerochan_fuuu_ni_makezu.png",
        "d32f573a15cf0391d514b19d0aaa68f12f584b808d0acddb9b356064eba177a9",
    ),
    "assets/thkaguyamod/textures/items/spellCard/LittleBugStorm.png": (
        "assets/five_difficulties_port/textures/item/spellcard/littlebugstorm.png",
        "6499d259ccfd413b717bbc8d8e2a27c6c36ba37142bcb2e998cb59c1b77b373a",
    ),
    "assets/thkaguyamod/textures/items/spellCard/MasterSpark.png": (
        "assets/five_difficulties_port/textures/item/spellcard/masterspark.png",
        "8952c25b2e748e2769682ff860a14b69201f2611bce9b6f5f8b6e2d1ce583b4d",
    ),
    "assets/thkaguyamod/textures/items/spellCard/MeteonicShower.png": (
        "assets/five_difficulties_port/textures/item/spellcard/meteonicshower.png",
        "2a1866aa91c80412aecf6bf838f973a59257f3fc15da397df16dc27ba4043a15",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Meteor_on_Earth.png": (
        "assets/five_difficulties_port/textures/item/spellcard/meteor_on_earth.png",
        "efc98a55be6b4cc06b6797985600b0de724735946dcabaf468a4124009664c30",
    ),
    "assets/thkaguyamod/textures/items/spellCard/MiracleFruit.png": (
        "assets/five_difficulties_port/textures/item/spellcard/miraclefruit.png",
        "16c44265fe1faa5b54dbd33b148f70d17ebe30ce4a2f62212d682eea8a4263d1",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Mishagujisama.png": (
        "assets/five_difficulties_port/textures/item/spellcard/mishagujisama.png",
        "6d7c6e2b6ab39a31ee24ab7159714b3d1c0d8cdcf4e6a88e731296f8c7f09690",
    ),
    "assets/thkaguyamod/textures/items/spellCard/MoonlightRay.png": (
        "assets/five_difficulties_port/textures/item/spellcard/moonlightray.png",
        "25b776227da4c670a95bae227c92cfbaa50d440f798ad00b1a7eef73ae9f3929",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Moses_no_Kiseki.png": (
        "assets/five_difficulties_port/textures/item/spellcard/moses_no_kiseki.png",
        "7d6644d819a3f6fe49b4320f9bf07370b144b6c9d857e8b4f9f9b8e798522cde",
    ),
    "assets/thkaguyamod/textures/items/spellCard/MusouFuuin.png": (
        "assets/five_difficulties_port/textures/item/spellcard/musoufuuin.png",
        "78c4688993b903709b5cca000fde824914429a1a3ac9afc1fa06c9c3858286fc",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Nami_to_Tubu_no_Kyoukai.png": (
        "assets/five_difficulties_port/textures/item/spellcard/nami_to_tubu_no_kyoukai.png",
        "e246579282a7519bce17ace36d8b8d3d9d431601fc95f6028656016db2310a3a",
    ),
    "assets/thkaguyamod/textures/items/spellCard/NightBird.png": (
        "assets/five_difficulties_port/textures/item/spellcard/nightbird.png",
        "65efa9f8c970391beb25058e23bed755657656dbc31b05b682c4cf02da677477",
    ),
    "assets/thkaguyamod/textures/items/spellCard/NijuuKokushichou.png": (
        "assets/five_difficulties_port/textures/item/spellcard/nijuukokushichou.png",
        "be72543a8335a4e628bc629196b586d2b3940195dd770c1a034b554f39330dd1",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Non-DirectionalLaser.png": (
        "assets/five_difficulties_port/textures/item/spellcard/non_directionallaser.png",
        "23b61bff37b9961a607c94f6107d78dd35f0c9618e71d56d65372f0a348cf85d",
    ),
    "assets/thkaguyamod/textures/items/spellCard/PerfectFreeze.png": (
        "assets/five_difficulties_port/textures/item/spellcard/perfectfreeze.png",
        "edc258dfe2e56f1108e562f1e7fb1b2affb7486e1e913344fd2f6cac6e0d0475",
    ),
    "assets/thkaguyamod/textures/items/spellCard/RedMagic.png": (
        "assets/five_difficulties_port/textures/item/spellcard/redmagic.png",
        "c32cb12e18cfae678f7567ca21ddd92c4ffefd928dd181f45523393e28d33ad0",
    ),
    "assets/thkaguyamod/textures/items/spellCard/SaikouRanbu.png": (
        "assets/five_difficulties_port/textures/item/spellcard/saikouranbu.png",
        "7d3273cd3b17d2f5ae061d02343aed2e6fc5bde21ec877f4a166c19538adf0c3",
    ),
    "assets/thkaguyamod/textures/items/spellCard/SatuzinDoll.png": (
        "assets/five_difficulties_port/textures/item/spellcard/satuzindoll.png",
        "47eae1fbfd4a5196bda468491a885fc47124dadd3722495813043d8a9a741f09",
    ),
    "assets/thkaguyamod/textures/items/spellCard/ScarletShoot.png": (
        "assets/five_difficulties_port/textures/item/spellcard/scarletshoot.png",
        "a219c8de036a18901730638482976c42632d9d6e182dddbf0ee768ad62267634",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Spear_the_Gungnir.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spear_the_gungnir.png",
        "551bf971863438cc0dc747078a5d2bcfcc54568d7f803b5f1e5b7e07792b52a4",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_frame.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_frame.png",
        "fbfc82ed35cfd6c4bceb054f9e347d2bc6ef813c71d0d2734187f369a98f4bf2",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_lv1.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_lv1.png",
        "9956bd80f3a44495f6d206367e104de61da722c06141f91ac15673a3cb4ddbc9",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_lv2.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_lv2.png",
        "4b013df9f8d8390667c44dec1cd653d29bc9f46b1c60742282f5ac9bd8fd3be9",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_lv3.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_lv3.png",
        "8067b6d67a8db53d97d33800f03f8c4c95e2c40f484bd4760eaa0b0bd29f385e",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_lv4.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_lv4.png",
        "b2a6df9c42e6a577319b2afa90511fea9db2071c1f2979b114ce9493e5fa8b67",
    ),
    "assets/thkaguyamod/textures/items/spellCard/spellcard_lv5.png": (
        "assets/five_difficulties_port/textures/item/spellcard/spellcard_lv5.png",
        "5d58a7e2b234457e77bb7a2ee7178660321082bc38d2f2017aa1f3c9e17665ab",
    ),
    "assets/thkaguyamod/textures/items/spellCard/StarbowBreak.png": (
        "assets/five_difficulties_port/textures/item/spellcard/starbowbreak.png",
        "2cc0c5d613176dd1d913e0c9145534512244823ce94b2b9a4d96e5f11c0adc72",
    ),
    "assets/thkaguyamod/textures/items/spellCard/StardustReverie.png": (
        "assets/five_difficulties_port/textures/item/spellcard/stardustreverie.png",
        "2fb5c28705d1f5ab3b236ec73dfa88a02362093628d0f075c28ef08fce60e9b4",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Yasaka_no_Kamikaze.png": (
        "assets/five_difficulties_port/textures/item/spellcard/yasaka_no_kamikaze.png",
        "446a1a7245c077e4104a1587abc6fb76701f7ff1999c0ffb32a3959b292fb862",
    ),
    "assets/thkaguyamod/textures/items/spellCard/YouryokuSpoiler.png": (
        "assets/five_difficulties_port/textures/item/spellcard/youryokuspoiler.png",
        "7d6c348bb62006cefd8dd9caa78ef9d926192a9f52d6496a3c5d2de64c3905df",
    ),
    "assets/thkaguyamod/textures/items/spellCard/Zenzinrui_no_Hisouten.png": (
        "assets/five_difficulties_port/textures/item/spellcard/zenzinrui_no_hisouten.png",
        "0ae16acc7cc6ebcc2fd3f929aa92c306eaad1f3cb192ef3b53806c20bfba9f23",
    ),
    "assets/thkaguyamod/textures/items/material/ShotMaterial.png": (
        "assets/five_difficulties_port/textures/item/material/shot_material.png",
        "6d4e0346e46f0a40081cc4e1c774b313976ef605a6560c29d0faca0a787dafda",
    ),
    # P10 laser item icons.
    "assets/thkaguyamod/textures/items/shot/MiddleLaser.png": (
        "assets/five_difficulties_port/textures/item/shot/laser.png",
        "28935db756daa479e5218568ab13a0619a58de2113124e730b2ea5bc654e46ff",
    ),
    "assets/thkaguyamod/textures/items/shot/ShortLaser.png": (
        "assets/five_difficulties_port/textures/item/shot/short_laser.png",
        "16a0949b86fd9626a2001de5116cd9a23f1afcbbe84d2eb5e254deda4374738c",
    ),
    "assets/thkaguyamod/textures/items/shot/LongLaser.png": (
        "assets/five_difficulties_port/textures/item/shot/long_laser.png",
        "6e25e32fde94582899e1e1bdac06d2be5000a55595830e0db29af9395c832b22",
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

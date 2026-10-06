# Five Difficulties X1 Preservation Port — P2 canonical X1 reacquisition

Date: 2026-10-07

Status: **CANONICAL ORIGINAL REACQUIRED AND VERIFIED**

## Source

Original addon thread post 54 still exposes the historical distribution Google Drive:

- bundle URL ID: `1NzSprhXvxaoPK6I8OJCxF2UqM6OCNaZt`
- title: `5難題+アドオン達.zip`
- Drive created/modified timestamp: 2019-07-03

The same post names:
`五つの難題MOD%2B ver2.90.1.X1-1.7.10.zip`

OpenEye independently indexes an X1 file with:
- exact size `4,596,892` bytes;
- exact SHA-256 endpoint:
  `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`.

## Reacquired outer bundle

Drive raw bytes:

- name: `5難題+アドオン達.zip`
- size: `4,548,944` bytes
- SHA-256:
  `9d8ea665ab8b925437fa2294f34051b8b9bdc6e9036c540f5c2a77432b689a98`

This exactly matches the prior PR #93 `SOURCE-INVENTORY.json` receipt.

Contained artifacts:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Add_Battler_Sakuya.jar | 26,002 | `18ccd13fcb3a7874024d1ac141183131fddfe972f5fab1ce2f1677051119c1d3` |
| Add_Last Judgment.zip | 47,066 | `2bbcb98fb6e5ee32ef509554e37fa56bbb4edb408a7a12788a15a9fb8742368a` |
| EntityModeTOHOU MAIDs 2.61.zip | 31,890 | `76470568cf1dc016e950badfb9458f567943e730c647043b467daaf070765b3f` |
| canonical X1 core | 4,596,892 | `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634` |

Every artifact hash matches the prior analysis receipt.

## Canonical X1 inner archive

Reacquired inner archive:

- version/name: 五つの難題MOD+ ver2.90.1.X1-1.7.10
- size: `4,596,892` bytes
- entries: `956`
- Java sources under `sources/java/`: `266`
- class files: `276`
- SHA-256:
  `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`

The canonical source/binary corpus is therefore available again for P2.

## Raw distribution policy

The raw third-party distribution is **not committed to this public TECH-HUB repository**.

P2 may:
- inspect the reacquired bytes locally;
- record hashes, paths and derived engineering facts;
- build private/local asset-overlay tooling.

P2 should not:
- commit original PNG/JAR/ZIP/source trees to this public repository merely because the port itself is intended for private use.

## First P2 target paths recovered

- `sources/java/thKaguyaMod/item/ItemHomingAmulet.java`
- `sources/java/thKaguyaMod/entity/shot/EntityHomingAmulet.java`
- `sources/java/thKaguyaMod/client/render/shot/RenderHomingAmulet.java`
- `sources/java/thKaguyaMod/ShotData.java`
- `sources/java/thKaguyaMod/THShotLib.java`
- `sources/java/thKaguyaMod/DanmakuConstants.java`
- `assets/thkaguyamod/textures/shot/HomingAmulet.png`
- `assets/thkaguyamod/textures/items/homingAmulet.png`

This clears the P2 evidence gate for exact Homing Amulet geometry/render reconstruction.

# Five Difficulties X1 Preservation Port — X1 evidence bridge

Date: 2026-10-07

Purpose: connect the active 1.20.1 implementation branch to the earlier evidence-backed 古文 analysis without pretending the raw X1 ZIP has been rematerialized in this session.

## Canonical ORIGINAL artifact

Previous analysis:
- PR #93: `docs(kobun): analyze 五つの難題MOD+ X1 ecosystem`
- PR head: `cb83cee43c241b45e473f01e00263adf4d1c188f`
- path root:
  `departments/minecraft/kobun/mods/itutu-no-nandai-plus/`

Outer user-supplied bundle:
- name: `5難題+アドオン達.zip`
- SHA-256: `9d8ea665ab8b925437fa2294f34051b8b9bdc6e9036c540f5c2a77432b689a98`
- entries: 4

Canonical core artifact:
- name: `五つの難題MOD+ ver2.90.1.X1-1.7.10`
- internal @Mod version: `2.90-1.7.10`
- Minecraft: `1.7.10`
- author-supported Forge/FML: `10.13.4.1614`
- SHA-256:
  `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`
- bytes: `4,596,892`
- ZIP entries: `956`
- class entries: `276`
- bundled `sources/java/`: `266`
- classfile major: `50`
- evidence basis: ORIGINAL_SOURCE + ORIGINAL_BINARY

The raw distribution is **not** committed to TECH-HUB.

## Why filename-only replacement is forbidden

Public telemetry contains other files with similar names/version strings and different sizes/hashes.

Examples include public `ver2.90.1` and `X1` filenames whose byte sizes differ from the canonical 4,596,892-byte artifact.

Therefore:

**Do not replace the canonical X1 artifact with a public mirror based on filename/version alone.**

Any reacquired candidate must match SHA-256
`6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`
before its raw source/assets are allowed to become implementation input.

## Original source paths already pinned by PR #93

Core:
- `sources/java/thKaguyaMod/ShotData.java`
- `sources/java/thKaguyaMod/LaserData.java`
- `sources/java/thKaguyaMod/THShotLib.java`
- `sources/java/thKaguyaMod/registry/DanmakuPatternRegistry.java`
- `sources/java/thKaguyaMod/registry/SpellCardRegistry.java`
- `sources/java/thKaguyaMod/registry/SpecialShotRegistry.java`
- `sources/java/thKaguyaMod/entity/shot/EntityTHShot.java`
- `sources/java/thKaguyaMod/entity/shot/EntityTHLaser.java`
- `sources/java/thKaguyaMod/entity/shot/EntityTHSetLaser.java`
- `sources/java/thKaguyaMod/entity/spellcard/EntitySpellCard.java`
- `sources/java/thKaguyaMod/entity/spellcard/THSpellCard.java`

Sakuya time:
- `sources/java/thKaguyaMod/entity/item/EntitySakuyaWatch.java`
- `sources/java/thKaguyaMod/entity/item/EntitySakuyaStopWatch.java`
- `sources/java/thKaguyaMod/event/THKaguyaTimeStopEventHandler.java`

Rendering:
- `client/render/shot/RenderTHShot`
- `client/render/shot/RenderTHLaser`
- `client/render/RenderSpellCard`

## Evidence documents used by P1

From PR #93:
- `HISTORICAL-MANIFEST.json`
- `SOURCE-INVENTORY.json`
- `CODE-MAP.md`
- `ACTION-VARIANT-ATLAS.md`
- `NON-SPELL-COMBAT-ATLAS.md`
- `SPELLCARD-ATLAS.md`
- `DANMAKU-PATTERN-TAXONOMY.md`
- `INPUT-ACTION-TAXONOMY.md`

These are derived records from the exact artifact and may be used for behavior contracts when the underlying claim is explicit.

They do **not** authorize inventing:
- unknown numeric shot/color IDs;
- exact render UVs not recorded;
- unobserved runtime interpolation;
- time-stop freeze categories not established by source/runtime;
- original PNG bytes that are not available in the current workspace.

## P1 evidence rule

A P1 implementation field must be tagged conceptually as one of:

- `X1_EXACT_STATIC` — exact value/branch recovered from ORIGINAL_SOURCE/BINARY analysis;
- `X1_STATIC_INFERENCE` — clearly labeled inference;
- `ROUNDABOUT_ENGINEERING_REFERENCE` — modern donor behavior, not X1 behavior;
- `UNRESOLVED_X1` — intentionally left unimplemented/fail-closed until raw/runtime evidence exists.

The current first P1 targets are chosen because PR #93 contains sufficiently explicit X1_EXACT_STATIC contracts:
1. red Homing Amulet normal/focus geometry and damage;
2. Sakuya Watch/StopWatch mode/range/duration values.

Visual sprite bytes and actual time-stop tick-category policy remain outside that boundary.

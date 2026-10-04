# 五つの難題MOD+ X1 ecosystem — 古文 analysis

Status: **EVIDENCE_BACKED static analysis / runtime NOT_RUN**

Historical lane: **古文**

This workspace analyzes the user-supplied Minecraft 1.7.10 distribution of **五つの難題MOD+ X1** together with four historically related addons. The supplied artifacts are the primary ORIGINAL evidence. The X1 core unusually contains its own `sources/java/` tree, so core findings can be checked against both ORIGINAL_SOURCE and distributed class bytecode.

## ORIGINAL — core

- Distribution name: 五つの難題MOD+ ver2.90.1.X1-1.7.10
- `@Mod` identity: `THKaguyaMod` / **Itutu no Nandai MOD+**
- Version declared by `@Mod`: **2.90-1.7.10**
- Minecraft: **1.7.10**
- Forge era: author X1 notes support for **10.13.4.1614**
- Artifact SHA-256: `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`
- Size: 4,596,892 bytes
- ZIP entries: 956
- Class entries: 276
- Bundled Java sources: 266
- Classfile major: 50
- Runtime: NOT_RUN
- License: UNKNOWN

The bundled `mcmod.info` is an Example Mod placeholder and conflicts with the actual `@Mod` identity, so it is not treated as authoritative identity evidence.

## ORIGINAL — supplied addons

| Artifact | Mod ID | Hard dependencies | SHA-256 |
|---|---|---|---|
| Add_Battler_Sakuya.jar | `add_angry_sakuya` | THKaguyaMod | `18ccd13fcb3a7874024d1ac141183131fddfe972f5fab1ce2f1677051119c1d3` |
| Add_Last Judgment.zip | `add_eiki_spell` | THKaguyaMod | `2bbcb98fb6e5ee32ef509554e37fa56bbb4edb408a7a12788a15a9fb8742368a` |
| EntityModeTOHOU MAIDs 2.61.zip | `TOHOmaidCore` | THKaguyaMod, lmmx | `76470568cf1dc016e950badfb9458f567943e730c647043b467daaf070765b3f` |
| Illusion Laser mod 2.2.jar | `Illusion_Laser_mod` | THKaguyaMod | `dd8f4d5c1397f11f5a86f8cb145b7645d9a092cb2b9f215292a2333c49c16c8c` |

Outer user bundle SHA-256: `9d8ea665ab8b925437fa2294f34051b8b9bdc6e9036c540f5c2a77432b689a98`.

## Main recovered technologies

1. **Data-driven danmaku primitives** — `ShotData` / `LaserData` describe projectile properties while `THShotLib` owns ring/sphere/spread/laser geometry.
2. **Pattern-level difficulty scaling** — `DanmakuPatternRegistry` changes count/span/speed/form tables by configured danmaku level.
3. **Spell-card behavior plugins** — `EntitySpellCard` is a world/lifecycle host; `THSpellCard` subclasses supply choreography.
4. **Special-shot plugin registry** — homing/diffusion/fall behaviors are registered and selected separately from base projectile entity logic.
5. **Persistent beam entities** — `EntityTHLaser` performs segment collision and supports attached/setting-beam patterns.
6. **Time-stop exemption contract** — spell behaviors may opt into special processing during stopped time.
7. **Addon-friendly core APIs** — Sakuya/Eiki/Maid/Laser addons extend the ecosystem without editing the core distribution.
8. **Ballistic trajectory solving** — TOHOU MAIDs computes elevation from gravity/speed/distance/height for thrown knives.
9. **Controller + effect entity split** — Illusion Laser uses a controller attached to the user while core beam entities retain collision/render semantics.

## Important boundaries

- The X1 core time-stop Forge `CanUpdate` handler is effectively a no-op; actual stop behavior is implemented by stopwatch/watch entities that repeatedly restore entity state.
- Legacy DataWatcher numeric slots, SRG method symbols, immediate GL11 rendering, Java object-serialized packets and direct client entity mutation are historical assumptions, not modern recommendations.
- TOHOU MAIDs directly links `illusion_Laser.Item_LaserCore` but does not declare Illusion Laser as a dependency. Contemporary crash evidence matches that hidden dependency.
- No runtime experiment was performed.
- Descendant/remake code is not used to rewrite ORIGINAL behavior.

## Documents

- [Historical manifest](HISTORICAL-MANIFEST.json)
- [Source inventory](SOURCE-INVENTORY.json)
- [Core technologies](CORE-TECHNOLOGIES.md)
- [Addon ecosystem](ADDON-ECOSYSTEM.md)
- [ERA context](ERA-CONTEXT.md)
- [Failure / repair lessons](FAILURE-REPAIR-HISTORY.md)
- [Modern extraction](MODERN-EXTRACTION.md)

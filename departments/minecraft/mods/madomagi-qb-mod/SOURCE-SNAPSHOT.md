# QB-MOD / Garnet-MOD — Source Snapshot (2026-10-07)

## Scope and tracks

- ANCHOR: Minecraft 1.20.1 + Forge — destination for reconstruction/backport. No claim is made that the legacy source compiles or runs on ANCHOR.
- COMPARATIVE / LEGACY: Minecraft 1.6.4, QB-MOD 1.6.4.082 + Garnet-MOD 1.6.4.082 — primary implementation evidence supplied by the project owner.
- FRONTIER: unresolved. No maintained upstream repository or later source snapshot has yet been pinned.

Evidence from other versions is not merged into 1.6.4.082 implementation claims.

## Supplied archives

| Role | Archive | Bytes | Entries | SHA-256 |
| --- | --- | ---: | ---: | --- |
| primary content MOD | QB-MOD.v.1.6.4.082.zip | 652672 | 437 | 52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e |
| framework/dependency | Garnet-MOD.v.1.6.4.082.zip | 103674 | 98 | 5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778 |
| alternate texture pack | TexturePack-01.zip | 42298 | 25 | 2f868b66ec3d4ea9baae91c8dc601d46b3215be067a17b7ad3ed02fddb636aec |

### QB-MOD inventory

- 156 Java source files under MCP/puellamagi/mods/
- 156 compiled .class files
- 94 PNG assets
- 1 cfg and 1 readme
- broad Java split: 76 entity, 54 client, 19 item, 2 block, 5 root/UI/bootstrap

### Garnet-MOD inventory

- 37 Java source files under MCP/garnet/mods/
- 37 compiled .class files
- 1 PNG asset
- 1 cfg and 1 readme
- broad Java split: 18 root AI/bootstrap, 9 entity, 7 client, 3 item

Java/class counts are now backed by an exhaustive structural correspondence pass: all 193 Java paths have a matching class path and all 193 classes carry the corresponding Java SourceFile basename. Representative `javap -p` surfaces also match source-derived subsystems. See `BINARY-SOURCE-CORRESPONDENCE.md`. This is strong structural correspondence, not a claim of full method-body/reproducible-build equivalence.

## Primary metadata

QB entrypoint locator:
- QB archive SHA above + MCP/puellamagi/mods/mod_QB.java:88-95
- @Mod version 1.6.4.082 with dependency after:Garnet-MOD
- @NetworkMod(clientSideRequired=true, serverSideRequired=false)

Garnet entrypoint locator:
- Garnet archive SHA above + MCP/garnet/mods/mod_Garnet.java:18-24
- @Mod version 1.6.4.082
- custom channels include Garnet and GarnetGun

The QB readme declares MinecraftForge + Garnet-MOD as prerequisites and says multiplayer installs both server and client. It expressly permits using the MOD in videos and modifying/referencing it, while prohibiting commercial use. Locator: QB archive SHA + readme.txt:6-18 after CP932 decoding. Garnet contains the same modification/reference permission. These readmes are usage-condition locators for this snapshot; they are not generalized into a modern open-source license.

## Configuration identity

MCP/QB-MOD.cfg defines:
- EasyMode=false
- GSLightLevel=10
- GSSpawning=20
- HeightCorrection=true
- SatelliteMode=false
- canWalpurgisSpawn=true

Code locator: QB archive SHA + MCP/puellamagi/mods/mod_QB.java:258-268.

## Acquisition / rights note

Raw ZIPs, source trees, compiled classes and original art are not committed to KNEEKURA-TECH-HUB. Only hashes, inventories, behavioral maps and derived engineering findings are retained.
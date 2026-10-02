# U06: Clumps Fabric and Connector, split-track static acceptance

**Static retrieval verified; compatibility remains UNKNOWN.** The exact beta.50 source ANCHOR and the released-stack COMPARATIVE are separate profiles and indexes. Every root and document matches its profile track. Opposite-track queries return zero hits. This bounded work followed Twilight Forest’s static pass and does not complete Connector runtime acceptance.

## Fixed real fixture

Check XP-orb merge and player-pickup translation prerequisites using [Clumps Fabric 12.0.0.4](https://modrinth.com/mod/clumps/version/hefSwtn6): a 21,987-byte JAR, 16 classes, two Mixin classes and a small event API surface. Its official changelog links commit `d249b4d25478e6044b0951f01b729c17b5860456`. This is a small real fixture, not a global size ranking. [A native Forge release exists](https://modrinth.com/mod/clumps/version/nAHGB5ls); the fixture does not recommend Connector over that option.

## ANCHOR: beta.50 source only

[Connector commit 7f68ac02291fde986119a3f5cab85436bed5c350](https://github.com/Sinytra/Connector/tree/7f68ac02291fde986119a3f5cab85436bed5c350) declares beta.50, Forge 47.4.6 and FFAPI 0.92.0+1.11.5+1.20.1. The ANCHOR profile contains only its **27 selected source documents in one root**, with **zero binary classes**. Matching beta.50 binary and actual resolved dependencies remain absent; the checked official GitHub/Modrinth release lists exposed no beta.50 release.

- Profile: `afd23ab348285bd2b3c2292d66ec72c7439c9f1b5bcd12110d858a846b8ed729`
- Index: `c375e7f9610f64672634232b48827794e9d9c70d974ffff3eb326e34fc3be8b0`
- Revalidated: 9 source query groups / 9 query pages; all 27 documents / 27 readback pages verified

The source traces Fabric metadata, recursive nested discovery and dependency/side selection, then intermediary-to-host remapping, Mixin/refmap and conditional AW conversion, entrypoint loading and cache behavior. These are source declarations; no stage was executed.

## COMPARATIVE: exact acquired released stack

This distinct profile excludes all beta.50 source. It captures original released artifacts, nested metadata, selected classfiles, separate Clumps/FFAPI source and selected Forge 47.4.6 context:

- [Clumps Fabric 12.0.0.4](https://modrinth.com/mod/clumps/version/hefSwtn6), SHA-256 `2eb70931dee86cef68c8538b8284c684225964632cd10e636ea938af6f66e6f7`
- [Connector beta.49](https://modrinth.com/mod/connector/version/1MQDrKN7), SHA-256 `e39acd37e162eb48cdfc6ae64776c13507a5ec3d4dd76ae4f39b5b79ca24d431`
- [FFAPI 0.92.6+1.11.15](https://modrinth.com/mod/forgified-fabric-api/version/g0MxcWXy), SHA-256 `3dd3f93c31122d928297220601f521e6a8a20356bafc7819bf4ddce4c2bb085d`

All advertised SHA-1/SHA-512 download hashes match. Connector’s beta.49 tag resolves to `f2e42536197749baa090759004a5d12e892a308a`; FFAPI’s release tag resolves to `84523ee99986a6b8b28ca2eff404b7702e7d5938`. Source/release association does not establish compiled-class equivalence. This released stack does not substitute for the beta.50 ANCHOR or alter any workspace dependency.

- Profile: `1b6f1c1154b31fd61c2192c1721104b000321ebbb96205a40cea42fd4a32a519`
- Index: `a2cb3581f47cea5c59f1fdecc38cda005d00351c516764e2af5db617346dcb20`
- Revalidated: 22 query groups / 38 query pages; 74 prepared classes; 337 complete documents / 632 readback pages
- Repeat preparation: same index, 74 cache hits, no selected class failures

Clumps’ release declares Fabric API required although its packaged metadata omits it. Original bytecode reaches FFAPI’s packaged Event/EventFactory surface, with `fabric` and `fabric-api` declared as FFAPI aliases. Two Java service-provider records and **nine conditional injector declarations** were inspected. Five mapping targets resolve directly; four exact-owner misses resolve only through explicit Entity superclass queries. Original misses remain recorded; runtime inheritance/refmap resolution was not simulated.

All **53 nested JARs** in the acquired released distributions were hash-inventoried. Actual host selection between bundled loader and MixinExtras candidates is unobserved; duplicate candidates alone prove neither conflict nor success. Connector Extras remains optional release metadata, and Launchpad/FRONTIER was not imported.

## Verification and remaining gates

Every returned locator was followed through complete, hash-checked readback within its own immutable index. Track isolation was explicitly tested. The earlier mixed-track snapshot is superseded and excluded from acceptance; its historical receipts remain unchanged. The focused intervention/mapping suite passed 23 tests using JDK 17.

Exact ANCHOR binary identity, resolved runtime dependencies/config/side/classloaders, actual remapping/Mixin application, ServiceLoader selection and observed XP behavior remain unresolved. Relations are PARTIAL and compatibility is UNKNOWN. No acquisition was added for this correction, and no game launch, upstream build, MOD edit, canonical/DB write or publication occurred. Performance and grep/IDE/Gradle comparison are unmeasured.

[Derived fixture, hashes, split identities and source locators](summary.json)

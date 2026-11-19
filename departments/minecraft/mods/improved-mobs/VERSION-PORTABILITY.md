# ImproveMobs 1.20.1 ANCHOR ↔ 1.21.1 FRONTIER

These are **different source snapshots**, not a merged implementation.

| Surface | ANCHOR: 1.20.1 Forge | FRONTIER: 1.21.1 NeoForge | Transfer boundary |
|---|---|---|---|
| Revision | [`029b8c20302a76bac1af9f5140e2abb6f73fea5c`](https://github.com/Flemmli97/ImprovedMobs/tree/029b8c20302a76bac1af9f5140e2abb6f73fea5c) | [`d495a4d617d38b841f275b174f7137e0644de13c`](https://github.com/Flemmli97/ImprovedMobs/tree/d495a4d617d38b841f275b174f7137e0644de13c) | source rev, not JAR checksum |
| Mod | 1.13.7 | 1.16.0.b | branch project property only |
| Toolchain | Java 17 | Java 21 | rebuild with appropriate toolchain |
| Loader dependency | Forge 47.1.3 dev property | NeoForge 21.1.233 dev property | API migration required |
| TenshiLib dependency | 1.20.1-1.7.2 in property | 1.21.1-2.3.0 | do not assume API/backward binary equivalence |
| Source layout | `common/`, `forge/`, `fabric/` | `common/`, `neoforge/`, `fabric/` | direct source rename not proof of identical behavior |
| Main config | Java fields, entity flags, lists | expression-based values, datapack overrides and Feature sets | explicit behavior/data migration |
| Block restoration | `BlockRestorationData extends SavedData` with `computeIfAbsent(loader,supplier,id)` | same core structure, `SavedData.Factory` with `HolderLookup.Provider` | versioned NBT/save APIs; **not** improved restoration fidelity |
| Path evaluation | `GroundNodeMixin` targets `WalkNodeEvaluator` and `BlockPathTypes`; extra collision caches | `WalkNodeMixin`/`PathFindingContextMixin`, uses `PathType`/context methods | major mappings and injection target changes; cannot paste Mixins |
| Actor tuning | blacklist/whitelist static flags | `EntityOverridesManager` per-entity datapack `EntityConfigProperties` / attribute configs | good candidate concept, new APIs |
| Item use | `ItemAI`/`ItemAIs` switch and Goal | `ItemUseRegistry` with implementation classes and MoveHandler | registry/strategy refactor; not binary interchangeable |
| Networking | Forge `SimpleChannel`, difficulty/config packets | `common/network` and NeoForge payload setup | new registration/serialization |
| Tracks | 106 Java files in observed source index | 136 Java files | no claim all were read |

**Frontier-only notable enhancement:** `EntityOverridesManager` explicitly resolves direct EntityType, tag and namespace overrides; supports a per-entity feature set and allow/deny/replace decisions for allowed breakable blocks and attributes. It is very relevant to a future modular invasion actor system, but current 1.20.1 ANCHOR does not contain that class. Independent backport needs design and Forge adaptation.

**No new reliable default full-world restoration in Frontier:** 1.21.1 `BlockRestorationData` still saves `BlockState`, time and computed drops. It still uses AIR-vs-other detection rather than a complete BlockEntity/transaction journal. Do not claim the newer version solved the strict reversible-siege requirement.

**Performance:** scoped caches in path evaluation may reduce duplicate block-type work per search; no profiled before/after or CPU savings asserted. Other performance Mixins have historical interoperability issues.

Portability proof pending: exact released JARs, TenshiLib closure, Forge 1.20.1 compile, Mixin method signature reconciliation, GameTests, dedicated server and frame/tick profiles.

Source: [1.20.1 `gradle.properties`](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/gradle.properties), [1.21.1 `gradle.properties`](https://github.com/Flemmli97/ImprovedMobs/blob/d495a4d617d38b841f275b174f7137e0644de13c/gradle.properties), [1.21.1 `EntityOverridesManager`](https://github.com/Flemmli97/ImprovedMobs/blob/d495a4d617d38b841f275b174f7137e0644de13c/common/src/main/java/io/github/flemmli97/improvedmobs/api/datapack/EntityOverridesManager.java), [both BlockRestorationData source branches](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/utils/BlockRestorationData.java), [frontier restoration](https://github.com/Flemmli97/ImprovedMobs/blob/d495a4d617d38b841f275b174f7137e0644de13c/common/src/main/java/io/github/flemmli97/improvedmobs/common/utils/BlockRestorationData.java).

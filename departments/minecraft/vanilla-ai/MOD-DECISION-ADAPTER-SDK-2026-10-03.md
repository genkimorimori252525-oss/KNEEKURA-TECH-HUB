# Source-specific Decision adapter SDK v1

This SDK follows native proof of the bounded Vanilla hooks. It extends the existing exact-subject Decision Model; it does not introduce another evidence database, implicit world scan, arbitrary plugin discovery or action authority.

## Registration and compatibility

The Java producer and retained Node consumer use explicit trusted registration lists. Metadata declares SDK/adapter versions, namespace/mod ID/version, Minecraft/Forge compatibility, mapped JAR SHA256, target class hashes, instrumentation, observer risk and supported epistemic levels. Registration rejects unknown descriptor fields, duplicate adapter IDs and invalid namespaced extensions.

Compatibility requires exact development-container bytes and corresponding class resources, rather than a matching version label alone. The source proof compares the resolved FML mod version, Minecraft/Forge versions, container hash and every declared class resource hash. Source IO is bounded and performed once per proven class loader. It does **not** attest post-Mixin transformed resident bytes. Field absence, source mismatch and unsupported cached structures remain unavailable.

`KneekuraDebugDecisionAdapter` provides producer `descriptor`, `supports`, `describeCapabilities`, `captureSnapshot` and `captureBurst` contracts. The snapshot receives the existing exact immutable context and finite entry/byte limits. Burst support must observe original calls; the current TF producer returns `NOT_EXPOSED` for it.

The retained `createDecisionAdapterRegistry` validates the same descriptor, bounds the retained input to its latest 64 compatible records, rejects mixed UUID/session/run/snapshot/process/Arena/selection identity and duplicate IDs, and gives callbacks frozen copies. Its authoring surface includes `describeCapabilities`, `captureSnapshot`, `captureBurst`, `emitStructuredFacts` and `emitVisualPrimitives`. Snapshot facts may remain sampled or derived; they cannot promote themselves into original invocation or causal claims. Namespaced facts, capabilities and derived primitives retain acquired source IDs. The registry is a trusted extension contract, not a security sandbox for executing arbitrary untrusted code.

## Twilight Forest ANCHOR implementation

Original universal JAR SHA256: `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`.

Actual ForgeGradle/Parchment development JAR SHA256: `7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a`, Minecraft 1.20.1 / Forge 47.2.0 / TF 4.3.2508 / mapping generation `parchment_2023.08.20-1.20.1`. [Mapped class ledger](TF-ANCHOR-MAPPED-BYTECODE-LEDGER-2026-10-03.json) records ten exact class/disassembly hashes. The shared Java/Node descriptor is tested for equality.

| Entity | Cached source-specific state | Explicit limit |
| --- | --- | --- |
| Hydra | Selected coordinator's seven stored head containers, head numbers, previous/current/requested states, clocks, assigned target/head UUIDs | Stored state/assignment is not an original transition or attack decision. |
| Snow Queen | Phase and beam flags, summon/drop/beam counters | Phase is separate from execution; snapshot adjacency is not an exact transition. |
| Knight Phantom | Local number, formation, clock and charge position | Local number does not establish leader/group identity. |
| Ur-Ghast | Tantrum/counters, wander factor and exact NoClipMoveControl cached steering/cooldown | Generated candidates and A* explanation remain unavailable. |

Private bytecode also verified `SynchedEntityData`/accessor/DataItem cached storage. Reading Synched Data does not call arbitrary getters: exact known map/item/accessor types and accessor identity are required, and `DataItem.value` is read directly. Custom implementations fail closed. TF getters/setters, phase transitions, controller ticks, searches and AI are not replayed by snapshots.

The existing explicit `--decision-snapshot` selection enables the source-specific snapshot alongside the baseline. The default remains OFF. `AI_DECISION` uses `kneekura.mod-decision-snapshot/v1`; acquired facts integrate into the same Decision Packet with a `twilightforest` namespace and the pinned source descriptor. `evidence-decision --channel mod_state` reads retained state and derived label primitives with complete identity. Labels are presentation, and no viewer layer is enabled automatically.

## Verification and remaining work

Motion/Decision contracts: **69 passed / 0 skipped**, including native Gson omitted-null regression. Portable source proof rejects wrong artifact, wrong class, shadowed resources and missing owners. Genuine Synched Data tests preserve cached values/dirty state and reject missing/custom items without invoking a custom getter. Genuine Forge API checks and all bridge compilation passed before the frozen native trial.

[Native cached-state acceptance](NATIVE-TF-CACHED-STATE-ACCEPTANCE-2026-10-03.md) retains 204 compatible AVAILABLE TF snapshots, 683 canonical records, clean ACK/drop0 and four read-only CLI proofs. Hydra automatic-next sentinel is explicit even when Gson omits null; omitted target/head references remain NOT_CAPTURED. All original-save 85 hashes match. Original MOD transitions, spatial/timeline presentation, representative behavior scenarios and controlled total observer-effect measurement remain pending. The NoAI=true fixture does not establish full Boss AI acceptance. No TF artifact, whole decompiled source or private world is committed.

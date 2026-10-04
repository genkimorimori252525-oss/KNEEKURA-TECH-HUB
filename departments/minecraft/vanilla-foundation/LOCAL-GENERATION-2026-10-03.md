# Local Foundation Map generation — 2026-10-03

Status: **GENERATED — EXACT MINECRAFT DISCOVERY SCOPE; NOT RUNTIME-LOADED PROOF**

This record continues the local execution handoff and PR #79's foundation head `57e52f9ef44c082daf7abbb0b0f5ada3a258a406`.

## Actual environment and export

The existing isolated target MOD workspace was clean at `53a84d06578632b5d123e3c2bb631b611bf830d7`.

The existing `kneekuraExportInputs` ForgeGradle task completed successfully, with no Minecraft launch and no build-script edits:

| Field | Actual value |
| --- | --- |
| Minecraft | 1.20.1 |
| Forge | 47.2.0 |
| Java compile toolchain | 17, Oracle |
| Gradle | 8.14.3 |
| Development namespace | Mojmap |
| Resolved artifact roots | 302, preserving compile/runtime order |
| Export unresolved dependency array | Empty |
| ForgeGradle implementation version | Not exposed by this export; retained as null |
| Declared mapping properties | Not exposed by this export; retained as null |

The actual Minecraft coordinate is:

`net.minecraftforge:forge:1.20.1-47.2.0_mapped_parchment_2023.08.20-1.20.1_at_51dcbf991ed04ea51c28694d5f40c4caa100537d`

The Parchment generation is evidenced by the resolved coordinate; it is an annotation generation, not an alternative runtime namespace. The access-transformer suffix belongs to this exact development artifact. The map does not claim pristine Mojang classes or unmodified access flags.

The compile and runtime Minecraft roots contain the same exact JAR bytes:

`1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`

| Fingerprint | SHA-256 |
| --- | --- |
| Exact export JSON bytes | `fc769a3d401eea3e59f1d55cf67fbd036f22e760663d1b323e811196f9b28d18` |
| Canonical resolution export | `1761d256bf343f54a2581674ac0fa3869a73860e8ac2ae8a215e227ce3ca4dbd` |
| Workspace source generation | `47d18edfd4fef1e77b8b740ab0be635d857f066e054823c89ea2bc6ed3187f57` |
| Build configuration | `a69f7b4807b317036874224e7f7dfe678cf1c51ae0b25ffcdfce99270b26ee2e` |

## Explicit capture scope

This map uses the **two actual resolved Minecraft class roots** from the export. Their original full-profile orders are retained as provenance in the private scoped manifest. The complete resolved manifest and all 310 excluded source/resource/configuration/other-dependency roots remain recorded privately.

The scoped profile declares `EXACT_MINECRAFT_CLASS_ROOTS_ONLY` and `OUTSIDE_EXPLICIT_MINECRAFT_DISCOVERY_SCOPE` exclusions. Its complete coverage means complete capture of these requested Minecraft roots. It does **not** mean complete capture of every target MOD/dependency source or class.

The whole export inventory has a separate Windows portability limitation: Python reports two long-path TacZ dependency roots unavailable while Node can read the same paths. That limitation has not been repaired or rounded into a successful whole-classpath capture.

The whole MOD output-generation status remains `UNVERIFIED` in this import because no new same-source build receipt was supplied. It is not upgraded by the static Minecraft map.

## Immutable identities and coverage

| Artifact | Identity |
| --- | --- |
| Captured profile | `7eea2fa8bd633cbb529edc04d10905e62478c427957020e544eb4389d78e16bc` |
| IndexSnapshot | `55a63559b62697c11e8ece0cd2fcb97d2db4730684789a31240b2c515f08ba06` |
| Foundation Map | `522cbb565d187f8e1e7b97140206f5ac11e8ca90719528bd661f875f184e34fd` |

The existing pipeline returned `OK` for the Foundation Map:

- 7,108 unique Minecraft class owners;
- 14,216 captured Minecraft class documents, preserving compile/runtime origins;
- 61,051 structural reference/inheritance/interface edges;
- 18,460 captured documents across the two JAR roots;
- 0 missing anchors, 0 ambiguous anchors, 0 ambiguous owners;
- 0 unreadable classes, 0 path/owner mismatches, 0 reference truncations;
- class budget 20,000; no budget truncation.

The IndexSnapshot itself remains `PARTIAL` for method-body preparation: automatic all-class `javap` traversal was not requested. This does not erase the retained class bytes or change the separate Foundation Map coverage.

## Discovery acceptance

The existing `foundation_map.inspect` path returned `OK` for all 13 required owners:

- `net/minecraft/world/entity/Mob`
- `net/minecraft/world/entity/ai/goal/GoalSelector`
- `net/minecraft/world/entity/ai/Brain`
- `net/minecraft/world/entity/ai/navigation/PathNavigation`
- `net/minecraft/world/entity/ai/control/MoveControl`
- `net/minecraft/world/level/pathfinder/PathFinder`
- `net/minecraft/world/level/pathfinder/NodeEvaluator`
- `net/minecraft/world/level/pathfinder/Path`
- `net/minecraft/world/level/pathfinder/Node`
- `net/minecraft/client/renderer/debug/PathfindingRenderer`
- `net/minecraft/client/renderer/debug/GoalSelectorDebugRenderer`
- `net/minecraft/client/renderer/debug/BrainDebugRenderer`
- `net/minecraft/network/protocol/game/DebugPackets`

The existing `DebugPackets` readiness anchor was correct for the real input. No anchor assertion was weakened or changed.

Relevant subsystem counts are Goal 77, Brain/core 44, Behavior 144, Memory 6, Sensor 24, Navigation 7, Control 10, Pathfinding 13, and Client Debug 35. These counts are discovery taxonomy, not proof of complete semantic research.

## Reproduction and boundaries

Use the existing explicit export/import and Foundation Map commands documented in [README.md](README.md). Retain an exact export, select the exported Minecraft roots explicitly if using this discovery scope, and preserve the full-manifest hash/exclusion provenance. Build with `--max-classes 20000`; inspect the owners listed above.

Private artifacts include the exact export, imported/scoped manifests, CAS, discovery responses and preparation logs. No JAR, world, full class/disassembly dump, machine path, owner credential or private runtime log is committed here.

An optional source-artifact export attempt entered ForgeGradle MCP download network IO despite `--offline`; its owned process was stopped and its failed attempt retained. The succeeding binary-only export did not require that source fetch.

K: per-blob durable writes were slow. The unchanged capture pipeline generated the scoped artifact on a capacity-checked internal temporary directory. All 9,130 copied/previously retained entries (122,619,362 bytes) were verified by SHA on K:. The retained inventory hash is `d2e14a24210626d640cd2c384b52d73d4c6861238776ba4582fbd04d6103eb45`. The temporary source CAS also remains retained.

Actual `foundation-map search` found the Ghast owner, four nested control/Goal owners and its model/renderer (7 results / OK). A second CLI search against the hash-verified retained K: store found GoalSelector without resolving dependencies or launching the game.

## Verification so far

- Existing Foundation Map tests: **7 passed** on Windows/JDK 17.
- Existing Motion/Decision foundation tests: **30 passed, 0 skipped**.
- Actual binary Forge export: **exit 0**.
- Actual scoped Foundation Map generation: **exit 0 / OK**.

Runtime/client scenarios, deep adapter implementation, observer-effect measurement and complete Vanilla AI semantic research remain separate subsequent work.

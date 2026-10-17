# Java reuse batch: evidence joins and remaining limits

This is a task-scoped review of the substantial model/geometry/parser/maid/input extension. It is not whole-target completion, a startup checklist, an instruction to install every reverse-engineering tool, or a claim that a recorded declaration is a recovered feature.

## Fixed inputs and status

- Artifact: YSM2.6.5 Forge1.20.1, SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
- Comparison source: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`; whole source/artifact equivalence and original symbol names remain unproven.
- Central correspondence map:669 rows,405 CONFIRMED/264 HIGH, byte-identical SHA-256 `dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30`.
- These later dossiers remain PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. They do not automatically add or promote central rows.

## Connected findings worth carrying into reuse

| Need | Connected evidence | Important boundary |
|---|---|---|
| Assemble model assets | [Composition](CLIENT-MODEL-COMPOSITION-RECOVERY-2026-10-17.md), [input carriers](MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17.md) | Player default animation fallback shares references; vehicle/projectile data have different inheritance paths |
| Understand animation data ownership | [Animation/controller carriers](ANIMATION-DATA-OWNERSHIP-RECOVERY-2026-10-17.md), [geometry defaults](GEOMETRY-AUTHORED-DEFAULTS-RECOVERY-2026-10-17.md) | Read-only containers, mutable arrays/elements, authored defaults and runtime state are different |
| Reproduce model-local text | [Language fallback](MODEL-LANGUAGE-FALLBACK-RECOVERY-2026-10-17.md) | A present locale map does not fall through to English per missing key |
| Integrate a Molang parser | [Lexer/diagnostics](LEXER-TOKEN-DIAGNOSTICS-RECOVERY-2026-10-17.md), [entry ownership](PARSER-ENTRY-OWNERSHIP-RECOVERY-2026-10-17.md) | Token classification differs from numeric acceptance; entry points differ in reader ownership and exception handling |
| Use typed functions and debugging | [Function guards](TYPED-FUNCTION-GUARDS-RECOVERY-2026-10-17.md), [debug delivery](DEBUG-MESSAGE-DELIVERY-RECOVERY-2026-10-17.md) | Invalid function context returns null, not variable0; formatting and client-task delivery have separate state/timing |
| Bridge a TLM entity | [Control](MAID-ENTITY-CONTROL-RECOVERY-2026-10-17.md), [registration](MAID-CONTROLLER-REGISTRATION-RECOVERY-2026-10-17.md), [render/capability](MAID-RENDER-CAPABILITY-RECOVERY-2026-10-17.md) | Remote-struct setters/callback are no-ops; registered empty class is not an implemented listener; fallback retrieval is not fallback drawing |
| Render first-person attachments/background | [Background/movement](CLIENT-VIEW-MOVEMENT-RECOVERY-2026-10-17.md), [texture boundary](NATIVE-TEXTURE-JAVA-BOUNDARY-RECOVERY-2026-10-17.md) | Early latch, initial-state mode3 submission and queued upload are not completed animated rendering |
| Route animation input | [Extra-key routing](EXTRA-ANIMATION-KEY-ROUTING-RECOVERY-2026-10-17.md) | Shortcut, wheel, lock and movement-stop paths apply different checks and local/remote ordering |

## One bounded integration check after the substantial batch

[JAVA-REUSE-BATCH-CHECKPOINT](JAVA-REUSE-BATCH-CHECKPOINT-2026-10-17.json) freezes35 unique cohorts:18 extension cohorts and17 explicit prior anchors, deduplicated from the relevant smaller manifests. It is not all-repository CI and does not alter earlier frozen receipts.

The recorded run passed5,765 integrity checks and357 corrupted-evidence controls in7.314seconds. It compared18 overlapping method snapshots and four repeated owner declarations with zero conflicts. The manifest contains968 distinct method/declaration snapshots and149 distinct owner declarations. These are evidence bookkeeping counts, including support/abstract/native declarations, NOT counts or percentages of independently recovered semantics.

The script requires the exact JAR and pinned source. It verifies the central-map hash before and after, invokes only the frozen cohort tools and compares the retained code/declaration representations. A passing check proves the specified evidence agrees with the supplied bytes/source and its corruption controls, not that all interpretation is correct or that the application works.

## Cheap navigation before expensive verification

Use [the locator](EVIDENCE-LOCATOR-2026-10-17.md) for query/role/topic selection, then [the one-file method viewer](MEMBER-EVIDENCE-VIEWER-2026-10-17.md) to list signatures or read one exact member. Neither ordinary lookup runs auditors, scans source, downloads tools or executes target code. The viewer's12 unit tests/six actual repository cases include native/abstract Code absence. One lexer sample reduced returned data from426,069 evidence-file bytes to2,714 summary bytes; this is one measured output-size example, not a completion percentage.

Only run a cohort or batch verification when it answers the current task. Do not routinely rerun this35-cohort batch for a documentation edit or ordinary lookup. Existing compact-index hashes are selective freshness checks, not proof that every new file is indexed.

## Claims that remain separate

- Exact bytecode, a candidate readable source and a decompiler view are corroborating representations, not proof of original unobfuscated names.
- Selected Vineflower comparisons and JDK-only contracts did not load/execute the target application. The numeric probe tests Float.parseFloat/Character.isDigit, not the target lexer/parser.
- No target game, GPU output, native renderer/decoder/free implementation, protected model parsing or native input validation was executed or recovered here.
- Forge/TLM/provider runtime availability, callback order, external implementation behavior and observed failures remain unestablished where explicitly bounded.
- Source-path presence in a broad role inventory does not mean that file's behavior was reviewed. A zero exact-symbol caller count does not close reflection, external code or native use.
- Static conditional failure paths are not observed bugs, and this research does not patch them to make upstream behavior look complete.

Continue from a concrete unresolved seam rather than recapturing covered classes for larger counts. Independent semantic review remains a distinct next validation stage before any additional confidence promotion.

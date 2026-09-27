# Implementation checkpoint — 2026-09-28

Status: **IN_PROGRESS / headless input-analysis and report-validation adapter implemented**.
Design: [v1.4](../design/2026-09-28-mod-ai-environment/DESIGN.md).
Base: `0e773ccf509d2a24c6dca3830cef18f38334b2cd`, design PR #72.
Implementation branch: `jolly/minecraft-mod-ai-impl-2026-09-28` (stacked on design branch; no main merge).

## Working in this change

- Explicit local root capture; immutable source, resource, outer JAR and inventory blobs; ordered scope/namespace/stage/track metadata; unresolved-input coverage.
- Snapshot-bound literal search and full paginated reads; raw bytes; explicit JDK disassembly preparation; exact owner/name/descriptor lookup; duplicate origins remain ambiguous.
- Verified cached disassembly reuse; static references with incompleteness warnings; research-only retrieval of existing department documents.
- Same-run normalized GameTest report checking, target/optional/unrelated result separation, observation identity/interval validation and no blind operation retry.
- JSON CLI and documented caller-supplied existing-runner delegation boundary. No new canonical store, remote service or scheduler.

## What remains — do not mark the product complete

1. Import actual resolved ForgeGradle/userdev inputs from a real 1.20.1 MOD workspace. The current manifest is an explicit capture input, not automatic Gradle resolution.
2. Connect an existing decompiler/remapper provider and mapping/intervention metadata. This change does not translate names or infer Mixin compatibility; javap is disassembly, not Java decompilation.
3. Attach existing Hub context-guidance/staging paths with their original provenance contracts. Current context is literal research retrieval, not canonical recommendations.
4. Complete Connector research in the existing queue after Twilight Forest. The added reference is a design pointer, not an acquired SourceSnapshot or a completed analysis.
5. Implement and compile the Forge 1.20.1 live observation adapter, authenticated session handshake, actual report producer, and existing runner wiring. The current CLI imports reports and intentionally cannot launch a game.
6. Run the real MOD-editing acceptance loop and U01-U06/A01-A24 in their declared environments. Local fixture tests below are not these product acceptance tests.

## Evidence and limits

Local verification: **102 passed, 0 failed, 0 skipped**, plus Python compileall.
Python 3.13.5, pytest 9.0.2, OpenJDK 21.0.11; Java fixtures compiled with `javac --release 17`.
The repository declares pytest >=8.3,<9. This run used the preinstalled pytest 9.0.2, not the declared dependency environment.
No pytest/JDK version compatibility beyond those observed is claimed.

The local workspace was a selected-file checkout with exact upstream pyproject and package initializer, NOT a full clone.
The complete pre-existing Hub/PostgreSQL test suite, package build, actual Forge compile, Minecraft, GameTest and client/runtime behavior were **NOT_RUN**.
Durable and remote workspace calls returned 429; container DNS could not resolve external package/repository hosts.
No runner/CI/Actions dispatch, production-world change, prior PR merge or automatic canonical promotion was performed.

`verification/local-run.json` records commands, scope, outcomes and tested file hashes. Full RED/GREEN logs are in the accompanying conversation artifact.

## Self-adversarial review

This was same-assistant code review, not an independent agent review.
Regression tests were added before fixes for lost outer-JAR/inventory blobs, cache-as-input recursion, existing symlink write escape, wrong-input cached disassembly,
missing evidence, invalid filters, malformed identity, world/config/adapter mismatch, optional-mode drift, unreadable directory omission,
JDK image changes and nonfinite/overflowing observations. Full references remain available despite preview limits.
A missing original class does not hide a still-readable pinned disassembly; its availability is marked separately.

## Resume without repeating work

Read this checkpoint, the design, the Python module and its tests. Reuse this implementation branch; do not recreate the department or overwrite PR #71/#72.
Start with the actual MOD workspace input importer/provider connection, then run a concrete MOD query/edit before expanding infrastructure.
Keep CI off and use the already approved local verification route. Preserve NOT_RUN until real evidence exists.

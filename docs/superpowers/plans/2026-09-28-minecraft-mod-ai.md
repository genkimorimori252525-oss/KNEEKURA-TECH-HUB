# Minecraft MOD AI implementation plan

> **Active continuation:** [unified asset/runtime implementation plan](2026-09-28-minecraft-mod-ai-unified.md).
> The historical plan and its CI-off note below are preserved. PR #73's later
> IMPLEMENTATION-STATUS allows standard hosted CI; the unified plan governs the
> new asset/client work. Existing verified server code is reused, not reimplemented.

Goal: implement the approved v1.4 contract as a small headless adapter outside the frozen knowledge core.
Spec: departments/minecraft/design/2026-09-28-mod-ai-environment/DESIGN.md at upstream 0e773ccf509d2a24c6dca3830cef18f38334b2cd.

Global constraints: no CI, no Actions dispatch, no silent Forge upgrade, no canonical promotion, no automatic game launch. Existing department and research queue remain intact.

## Tasks / interfaces
1. `minecraft/storage.py`: canonical JSON, bounded CAS and ordered ProjectProfile capture. `capture_profile(manifest, base, store)` returns a hashed profile with exact input coverage. Tests: version/classpath/config changes, unsafe archives, unavailable roots, immutable bytes. RED then GREEN.
2. `minecraft/index.py`, `minecraft/bytecode.py`: immutable snapshot and paginated search/read, optional explicit JDK javap preparation (never execute a MOD). `prepare_index`, `search`, `inspect_document`, `find_symbols`; exact descriptors, per-origin ambiguity, coverage, stale cursors. Tests include real javac --release 17 fixture class/JAR and deliberate failures. RED then GREEN.
3. `minecraft/verification.py`: normalized GameTest report oracle, run-bound observations, world/budget gate, no execution on reads. Tests: zero tests, optional target failure, unrelated failure, epoch/build mismatch, missing observation fields. RED then GREEN.
4. `minecraft/__main__.py`: JSON CLI profile/search/inspect/context/validate/observe, docs and seeded Connector research reference. E2E subprocess tests including exit codes and no ambient execution.
5. Whole-change adversarial review; run all available tests; publish an isolated branch/PR with skip-CI; retain machine-readable evidence and remaining acceptance gaps.

Pre-flight: profile -> index -> query must share identity including unresolved roots; run validation consumes profile/index IDs but must not interpret an index as proof of build/runtime validity.
Ruling: remote Love-Github workspace and Durable state both returned 429; container cannot resolve external hosts. Use a separate local selected-file checkout with exact upstream base recorded, and connector Git object APIs for publication. Do not claim an unrun full repository suite or real Forge game test.
Ruling: source/bytecode and verification adapters are deliverables, not permission to call the entire 30-case product acceptance complete. Real Minecraft workspace integration and a real MOD-editing loop remain acceptance requirements when those inputs are available.

Execution checkpoint: the headless adapter and its local fixture tests are implemented; see departments/minecraft/mod-ai/IMPLEMENTATION-STATUS.md for outstanding product acceptance. The full environment is not complete.

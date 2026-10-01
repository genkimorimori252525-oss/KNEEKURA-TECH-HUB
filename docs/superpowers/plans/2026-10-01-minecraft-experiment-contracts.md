# Minecraft Experiment Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start X0/X1 with a strict, inert request/result boundary and exact existing-CAS evidence import, then connect only an audited LAB-owned adapter.

**Architecture:** TECH HUB owns experiment intent, immutable request bytes and result validation. LAB owns runtime, Arena, actions and snapshots. An import validates content and linkage; it does not authenticate that a runtime observation happened or turn execution completion into gameplay success.

**Tech Stack:** Python 3.11+, existing Store/CAS and pytest; LAB Node ESM and Forge 1.20.1 stay in their repository.

**Spec:** `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md`

## Global Constraints

- no new Evidence database
- no caller-supplied executable path
- no arbitrary Blockbench/Minecraft script
- no automatic retry after uncertain mutation
- no interpretation of action completion as gameplay PASS
- no production world
- TECH HUB TaskContext never executes an experiment
- Exact observed LAB main at audit: `21959d439960d112d05c4c3ee44e54e353246d4e`; Arena/action/fencing are prerequisites, not presumed present
- Request validation is pure. Preparation/import may write only the existing caller-selected Store, never launch or contact a service
- Completion of these source tasks is not X2–X7 runtime acceptance

## Review Focus

- A result with valid shape but unrelated request/build/snapshot must be rejected before any persistence
- An interrupted action or cleanup must retain UNKNOWN and cannot carry definitive behavior assertions
- Imported caller reports are not authenticated runtime evidence merely because a CAS hash matches
- A build-only repair comparison must explicitly declare changed target identity fields; setup/assertions/cameras stay fixed
- A later resource/config change cannot reuse a prior PASS as current evidence

### Task 1: Strict request and result schemas (X0)

**Files:** Create `src/kneekura_tech_hub/minecraft/experiment_contract.py`, `tests/test_minecraft_experiment_contract.py`.

**Interfaces:** `validate_experiment_request(value: dict) -> dict`, `validate_experiment_result(value: dict, request: dict) -> dict`, `experiment_binding(request: dict) -> dict`, `compare_requests(before: dict, after: dict, changed_target_fields: list[str]) -> dict`.

The request has exact fields: schema_version=1, experiment_id, generation, target, arena, subjects, initial_state, actions, observation_scopes, visual_rig, assertions, budgets. Target contains profile_id/index_snapshot_id/build_artifact_hash/source_revision/dirty_hash/config_hash/resource_hash. Arena has arena_id/preset/baseline_hash/bounds. Subjects bind a stable subject_id to exact UUID and resource entity type. Actions are strictly typed `wait_ticks`, `teleport_subject`, `use_item`, `set_block`; no strings interpreted as raw commands. Budgets cap 120000ms, 32 total actions and 16 captures. Initial-state and action IDs share one namespace. Numeric payloads are finite and bounded; world mutation coordinates stay inside declared arena bounds. Assertions are explicit typed checks with predeclared expected values and stable IDs.

Result execution completion, action completion, cleanup and per-assertion outcomes are separate. Raw/derived/interpretation evidence kinds remain separate. Evidence references must resolve within the result inventory. Nondefinitive statuses remain UNKNOWN/NOT_RUN/NOT_TRACKED/NOT_RENDERED/NOT_LOADED/INCONCLUSIVE rather than flattening them. The validator establishes consistency, never truth of a reported PASS.

- [ ] Write failing tests for accepted detached bounded payload and unknown/authority fields, bool-as-int, duplicate IDs, unknown subjects, out-of-bounds actions, stale identities, missing evidence and contradictory UNKNOWN/PASS
- [ ] Run `python -m pytest -q tests/test_minecraft_experiment_contract.py`; expected missing API failure
- [ ] Implement strict validators and deterministic binding using existing canonical/key_for
- [ ] Run focused tests; expected all pass, no network/process/runtime
- [ ] Commit the reviewed source and test changes

### Task 2: Existing-CAS preparation, import and stale/compare checks (X1 boundary)

**Files:** Create `src/kneekura_tech_hub/minecraft/experiment_bridge.py`, `tests/test_minecraft_experiment_bridge.py`.

**Interfaces:** `prepare_experiment(store: Store, request: dict) -> dict`, `load_experiment(store: Store, request_hash: str) -> dict`, `import_experiment_result(store: Store, request_hash: str, result: dict) -> dict`, `inspect_experiment_result(store: Store, result_hash: str, current_target: dict | None = None) -> dict`.

Preparation requires the exact captured index/profile and source revision/dirty hash; checks artifacts exist as CAS bytes. Imported result references an exact raw LAB RunSnapshot content hash. Snapshot schemaVersion/snapshotId/debugSessionId/runId/processEpoch and `techHub` binding must match the frozen request. LAB's own snapshotHash is retained separately and never confused with the raw-file CAS content hash. Import requires every evidence blob already in Store and verifies declared sizes before writes. Output retains `provenance=IMPORTED_LAB_REPORT`, `runtime_attestation=NOT_ESTABLISHED`, separate execution/assertion summaries and immutable provenance. Live attestation must be established through a future authorized adapter; caller JSON cannot assert it. Unknown completion recommendations are read-only reconciliation.

- [ ] Write failing tests for request/index mismatch, wrong snapshot binding, missing/corrupt artifact bytes, rejected result leaving no new blobs, identical import idempotency, retained UNKNOWN and stale current target
- [ ] Run `python -m pytest -q tests/test_minecraft_experiment_bridge.py`; expected missing API failure
- [ ] Implement using existing Store only; validate the complete import before storing/pinning
- [ ] Run both focused suites and full repository suite with the registered JDK17/dependency cache environment; report cached-dependency/DB skips explicitly
- [ ] Commit source and evidence docs after independent review

### Task 3: Audited LAB owner prerequisites and handoff

**Files:** LAB-owned paths and exact interfaces are fixed by the fresh X0 audit, not invented here.

- [ ] Freeze the audit report and smallest owner-repo execution plan
- [ ] Add the exact `techHub` request binding to the immutable RunSnapshot construction, preserving existing identity checks
- [ ] Implement missing Arena/action/mutation fencing in LAB under its own tests before any live bridge execution
- [ ] Retain X2–X7 as explicit incomplete gates until their source, real runtime and visual benchmark evidence exist; X8 is conditional and cannot be preclaimed NOT_NEEDED

### Task 4: Explicit offline CLI and honest TaskContext availability

**Files:** Create `src/kneekura_tech_hub/minecraft/experiment_cli.py`, `tests/test_minecraft_experiment_cli.py`; modify `connected_cli.py`, `task_routing.py` and exact inventory regression tests.

**Interfaces:** `experiment validate --request`, `prepare --request`, `inspect-request --request-hash`, `import-result --request-hash --result`, `inspect-result --result-hash [--current-target]`, `compare --before --after [--changed-target FIELD]`. No execution/launch route exists. The new twelfth TaskContext capability `experimental_runtime` is `surface=UNSUPPORTED, readiness=BLOCKED, reason_code=LAB_RUNTIME_BACKEND_UNAVAILABLE` with fixed missing owner prerequisites. This is a source-start status, not X7 acceptance. No new task intent or registry state is introduced.

- [ ] Add CLI dispatch/subprocess tests for explicit offline operations and malformed file redaction, with process/network callbacks forbidden inside dispatch
- [ ] Watch them fail, implement thin routing to Tasks1/2, and update the exact command/capability inventory assertions
- [ ] Run focused CLI/task suites and the full aggregate; preserve existing semantics and 12-capability output bound

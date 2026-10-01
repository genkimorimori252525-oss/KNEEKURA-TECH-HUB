# Minecraft scoped-control transport implementation plan

> For agentic workers: execute inline using the planning, test-driven-development and verification skills. Parent integration owns independent review and publication.

**Goal:** Add a separately registered, bounded LAB scoped-control transport and private CAS import while retaining inert TaskContext planning.

**Architecture:** Keep the existing registration-only adapter unchanged. Reuse its bounded file/process helpers and the existing Store; the LAB journal remains the only runtime replay/order authority. Validate all export bytes before importing their complete inventory.

**Tech Stack:** Python, pytest, Node protocol fixtures

**Spec:** `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md`

## Global constraints

- Source-only tests; no actual runtime, game, editor, deployment or publication
- New backend `kneekura.lab.scoped-control.v1`, pinned executable, complete module closure, private owner config and owner envelope
- Runtime attestation remains `NOT_ESTABLISHED`; submissions are never completed gameplay/visual results
- Timeout or uncertain outcome retains uncertainty and never retries
- Existing CAS only; no second replay ledger
- Snapshot 2 MiB, individual evidence 16 MiB, complete result evidence 64 MiB

## Review focus

- Legacy registry cannot dispatch scoped-control commands
- Owner/run/request mismatch or changed pinned source fails before spawning
- Process failure after submission retains a private, redacted UNKNOWN receipt
- Export inventory aliases, extras, missing blobs, symlinks, oversized files and changed bytes fail closed
- Explicit uncertain control receipt blocks every side-effecting TaskContext recommendation

## Task 1: Add bounded scoped-control transport

Files: create `minecraft/experiment_control.py`, test `tests/test_minecraft_experiment_control.py`

- [x] Write and run failing tests for separate registry, owner-envelope binding, typed commands, process failures and redacted receipts
- [x] Implement `inspect_registry`, `inspect_owner`, `submit_action`, `request_capture`, `inspect_action`, `export_result`, `inspect_receipt` with fixed commands and bounded outputs
- [x] Verify focused tests and unchanged legacy adapter tests

## Task 2: Import complete private exports

Files: create `minecraft/experiment_export.py`, test `tests/test_minecraft_experiment_export.py`

- [x] Write and run failing tests for bounded whole-inventory hash validation, private snapshot, malformed exports and no persistence before validation
- [x] Implement `import_export(store, registry, request_hash, manifest_hash)` using only fixed hash-derived paths beneath owner inputRoot
- [x] Verify focused CAS/export and retained-report tests

## Task 3: Expose explicit CLI and inert context

Files: modify `experiment_cli.py`, `connected_cli.py`, `task_context.py`, `task_routing.py`; add CLI/context tests

- [x] Write and run failing tests for fixed CLI commands and inert context registration/receipt inputs
- [x] Add explicit control commands and optional `experiment_control_registry` / `experiment_control_receipt_hash` inputs
- [x] Verify no subprocess/write from TaskContext, no execute/launch route, and all side-effect recommendations suppressed for uncertain control
- [x] Run full suite, report all failures, commit source-only implementation for parent review

Ruling: Explicit parent instruction already authorizes source implementation and isolated worktree; no additional planning approval gate. Parent owns final integration review. Known sandbox ancestor-path baseline failure must remain unchanged.

Verification: 151 focused transport/export/context/legacy tests passed. Final full suite after all guard additions: 3,247 passed, 145 skipped; only the preexisting `tests/test_minecraft_asset_guard.py::test_private_parent_validation_allows_real_external_directory` sandbox ancestor-path failure. The protection remains unchanged. All protocol, capture-budget, contradictory-summary, derived-export-overlap and same-request/different-run fixes were observed RED then GREEN. `git diff --check` passed. Source commit: `c7bc953`; parent integration owns independent review and publication.

Ruling: A capture index denotes a complete Cardinal-4 slot and consumes four units of the retained capture budget, matching LAB. Source transport never claims capture completion.
Ruling: Private export destinations stay outside and do not contain the sealed run; the actual hash-derived export directory is checked, including ancestor configurations.
Ruling: A finalized manifest does not promote result provenance or runtime attestation. Snapshot run/session/epoch linkage must also match the separately pinned owner.

## Task 4: Carry explicit owner cleanup through the same transport

- [x] Add failing tests for fixed `request_cleanup` and `inspect_cleanup`, conservative cleanup summaries, uncertain failure retention, inert TaskContext and rejection of extra CLI arguments
- [x] Extend existing transport and CLI with those two commands; no new modules, raw reset arguments, automatic cleanup, or replay ledger
- [x] Extend the actual paired source fixture with requested/inspected cleanup and preserved UNKNOWN cleanup result
- [x] Run focused, paired and full source regressions; parent retains integration and publication ownership

Ruling: This is the owner's existing one-reset allowance, explicitly requested by the caller. A pending or uncertain cleanup receipt only recommends read-only `experiment.inspect_cleanup`, and never claims cleanup was applied or confirmed.
Ruling: Every explicitly selected cleanup receipt retains reconciliation, including a reported `VERIFIED` reset with evidence. Supported reset classes cannot establish that earlier experiment uncertainty or unsafe state has cleared; no cross-receipt ledger is introduced.

Cleanup verification: 174 focused TECH tests passed; the updated real Python-to-Node source gate passed with requested cleanup, marker-only UNKNOWN inspection, fresh-Store duplicate fencing, and UNKNOWN imported cleanup. Final full TECH regression on source commit `30c8553`: 3,270 passed, 146 skipped, with only the unchanged `tests/test_minecraft_asset_guard.py::test_private_parent_validation_allows_real_external_directory` sandbox ancestor-path failure. A separate LAB `test:ci` run hit the source-only owner launch test's conservative teardown `live === false` assertion (`null` observed); its isolated rerun passed and parent integration owns that diagnosis. No stop-state protection was weakened.

## Task 5: Carry explicit bounded owner trigger watching

- [x] Add RED tests for optional hash-pinned trigger config, retained request bounds, fixed watch DTO, operation-specific timeout, ambiguous receipts and inert context
- [x] Extend the fixed source module closure, optional owner envelope validation and explicit `watch-triggers` command
- [x] Exercise actual paired Node source trigger dispatch and private evidence import; retain conservative outcomes
- [x] Run focused and full source checks, report the existing ancestor fixture failure, and commit for parent review

Interfaces: `watch_triggers(store, registry, request_hash)` emits only schemaVersion, operation and requestHash. The pinned private owner may add `triggerConfigHash` referencing the immutable `control/owner-trigger-config.json`. The selected source is `ARENA_EXIT`; config bounds and finite capture slots are validated against the retained request. Watch replies contain only common identity/status fields and unique bounded `captureWindowIds`; no capture completion is inferred.

Ruling: Only explicit watch dispatch may extend the process deadline to the retained time budget plus the registered ordinary timeout, at most 130 seconds. Pinning/preflight and ordinary commands keep their existing at-most-ten-second deadlines. Every watch receipt retains read-only owner reconciliation because a stopped observer cannot prove capture completion or clear prior uncertainty. Parent owns independent final review; runtime execution and publication remain deferred.

Trigger verification so far: 55 focused TECH trigger tests passed, including each new module omission/tamper case and a null optional hash regression observed RED then GREEN. The actual Python-to-Node paired gate passed after detecting a LAB timestamp precision mismatch; its producer keeps canonical microsecond timestamps to retain coverage. The fixture proves explicit reserved capture marker/deadline, partial window retention, no second watch after uncertain reservation, six-blob private import, and inert read-only reconciliation. Full source regression on frozen implementation `255f8ea`: 3,325 passed, 146 skipped, with only the unchanged `tests/test_minecraft_asset_guard.py::test_private_parent_validation_allows_real_external_directory` sandbox ancestor-path failure. All 674 tracked source files and the LAB paired fixture matched their tested manifests afterward. Independent X5 review found no remaining important source issue, and its final paired run passed in 17.12 seconds. Hosted paired tests remain uncompleted before tests; real runtime acceptance stays deferred.

# LAB TECH HUB Bridge Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a testable, inert LAB-owned identity/material/command-journal foundation and truthful bounded stop verification, while keeping real experiment execution unavailable.

**Architecture:** Extend LAB's existing Node supervisor and immutable RunSnapshot. A trusted local registration names fixed input files; experiment bytes cannot supply executable paths, environment, shell commands, or authority. New Arena/action modules validate intent and durable outcomes but have no Minecraft mutation backend in this slice. All future execution remains through LAB-owned typed Java controls.

**Tech Stack:** Existing Node ESM, built-in fs/crypto/node:test only; current Java Forge source remains unchanged in this foundation slice. Node 20 compatibility.

**Spec:** TECH HUB `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md`; LAB `docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md`; fresh audit `docs/KNEEKURA_TECH_HUB_BRIDGE_SOURCE_AUDIT_20261001.md`.

## Global Constraints

- Exact audited LAB main: `21959d439960d112d05c4c3ee44e54e353246d4e`.
- no new Evidence database
- no caller-supplied executable path
- no arbitrary Blockbench/Minecraft script
- no automatic retry after uncertain mutation
- no production world
- no interpretation of action completion as gameplay PASS
- no runtime launch, workflow dispatch, public push, or runtime config edit during this implementation task
- Use only local test fixtures; existing fake-target Node process tests are source-level Supervisor tests, never Minecraft acceptance
- Registered/material-file digests prove bytes read on disk, not which bytes the JVM loaded
- Imported/provided identities are linkage, not runtime authentication; `runtime_attestation=NOT_ESTABLISHED` remains mandatory in this slice
- No posthoc RunSnapshot edits; techHub binding participates in the initial write-once snapshot hash
- No executable bridge CLI, scheduler, daemon, arbitrary callback in request JSON, or second evidence store
- X2 Arena execution, Forge actions, camera barriers, X3–X7 acceptance remain BLOCKED after this slice

## Review Focus

- Cross-language hash differences: exact Python-produced CAS bytes retain their original hash; Node must not reserialize and silently change identity
- Traversal/symlink/oversized/replaced files: registrations only resolve files beneath trusted roots, read regular bounded files, reject escape and byte drift
- Crash/retry/concurrent idempotency: duplicate payload cannot re-execute; key reuse with new payload fails; incomplete accepted outcomes become UNKNOWN
- False cleanup success: inspection errors, still-live owned processes, PID reuse and nonzero kill attempts never become verified STOPPED
- Fake readiness: an apparently valid Arena/reset receipt or matching hash never upgrades a contract-only surface into proven Forge behavior

## Source/workspace status

This work copy is an isolated writable copy of the 224 hash-verified upstream blobs. It has no Git metadata. Do not create a synthetic upstream history or report a commit/push. Publish later through an authorized exact-base repository path, after reviewing a complete diff. All upstream sources are now materialized. Run the full source CI script; separately report the known local browser requirement in npm test.

## File/API inventory

| File | Responsibility / public APIs |
|---|---|
| NEW `debug-workspace/bridge/registration.mjs` | `validateTechHubBinding(value)`, `readBridgeInputs(registration, options)`, `registerBridgeRequest({runtimeRoot, registration})`, `loadBridgeRegistration({runtimeRoot, requestHash})` |
| NEW `debug-workspace/bridge/materials.mjs` | `readRegisteredFile({root, relativePath, expectedSha256, maxBytes})`, `verifyBridgeMaterials(registration, binding)` |
| NEW `debug-workspace/bridge/arena-contract.mjs` | `validateArenaContract(value)`, `validateActionEnvelope(value, arena, identity)`, `validateResetEvidence(value, arena, identity)` |
| NEW `debug-workspace/bridge/action-journal.mjs` | `beginAction({runDir, arena, identity, action})`, `recordActionOutcome({runDir, identity, idempotencyKey, outcome})`, `readActionOutcome({runDir, identity, idempotencyKey})` |
| NEW `debug-workspace/process-stop.mjs` | `verifyProcessesExited(records, options)` bounded injectable inspection helper |
| MODIFY `debug-workspace/core.mjs` | Optional trusted registration lookup before spawn; initial snapshot binding and material observations; verified stop integration; preserve old non-bridge run shape |
| MODIFY `debug-workspace/evidence/broker.mjs` | Supported coherence-mode allowlist; reject ATOMIC_SNAPSHOT/unknown labels |
| MODIFY `debug-workspace/evidence/finalize.mjs` | Preserve independent shutdown completeness and verified cleanup; do not finalize a still-live/unknown process as a clean bridge result |
| NEW `debug-workspace/bridge/tests/registration.test.mjs` | Exact bytes/binding/material safety and immutable registration tests |
| NEW `debug-workspace/bridge/tests/arena-journal.test.mjs` | Bounds/identity/revision/reset schema and durable unknown-safe journal tests |
| NEW `debug-workspace/bridge/tests/stop-snapshot.test.mjs` | Snapshot initial binding and bounded cleanup injected-inspector tests |
| MODIFY `debug-workspace/evidence/selftest.mjs` | Rejection of unsupported coherence labels; existing evidence regression tests |
| MODIFY `package.json`, `debug-workspace/README.md` | `test:bridge-foundation` script and precise readiness/verification boundary |

## Contract decisions

### Registration (trusted operator input, never embedded inside ExperimentRequest)

A registration object has exact keys:

```text
schemaVersion: 1
trustedRoot: absolute directory selected by operator
requestFile: relative file path
bindingFile: relative file path
assertionsFile: relative file path
materials:
  buildArtifact: { relativePath }
  configArtifact: { relativePath }
  resourceArtifact: { relativePath }
```

`readBridgeInputs` reads regular files below trustedRoot (no symlink component, no traversal/absolute path). Bounds: request 128 KiB, binding 64 KiB, assertions 256 KiB; buildArtifact 64 MiB, configArtifact 1 MiB, resourceArtifact 16 MiB. These are source-foundation limits, not execution/capture budgets. Stream material hashing; no arbitrary directory crawl. Reject duplicate JSON object keys in request/binding/assertions to avoid cross-language ambiguity. Parsed object trees may contain only JSON primitives, arrays and plain maps, and finite safe numeric values. Reject malformed UTF-8 instead of replacement decoding.

Binding is the shared TECH HUB object: `schema_version=1, experiment_id, generation, request_hash, target, arena_id, arena_baseline_hash, assertions_hash`. Exact target keys: `profile_id, index_snapshot_id, build_artifact_hash, source_revision, dirty_hash, config_hash, resource_hash`. Hash fields are lowercase 64 hex; source_revision is a Git revision string limited to 40/64 lowercase hex; generation is positive safe integer; experiment/Arena IDs use bounded ASCII identifiers. Preserve all fields exactly; no credentials or execution fields.

- `request_hash = SHA256(exact request bytes)`; verify request experiment/generation/target/Arena identities agree with binding.
- `assertions_hash = SHA256(exact assertions bytes)`; parsed assertions must deep-equal request.assertions. No JS recanonicalization of Python 1.0/exponents/-0.0.
- Each material's raw byte digest equals the relevant target hash. This first slice handles single files/archives; it does not claim a digest of a manifest proves referenced directory members or JVM-loaded content.
- Registration output is write-once `<runtimeRoot>/bridge/registrations/<request_hash>/registration.json` plus exact `request.json`, `binding.json`, `assertions.json`. It contains normalized safe paths, file digests/sizes and `runtimeAttestation: NOT_ESTABLISHED`.
- Same request hash + identical registration is idempotent; different content/path/material registration for the same identity fails `REGISTRATION_CONFLICT`.
- Use CREATE_NEW reservation + atomic same-directory file commits. An incomplete reservation is `REGISTRATION_INCOMPLETE`, never a successful registration. No deletion or automatic recovery of uncertain state.

### Supervisor hook

`launchDebugRun(config, repoRoot, options)` may receive only `options.bridgeRequestHash` for this feature; never a raw binding/executable/request object. Lookup is within its existing configured runtimeRoot. Before spawning, validate the immutable registration, request/material bytes, target source commit/dirty fingerprint mapping and exact observer identity. Because dirty_hash and LAB fingerprintSha256 are different algorithms, compare source_revision directly and retain separate measured LAB dirty/fingerprint facts; do not claim dirty_hash verified until a shared dirty fingerprint contract exists. Bridge registration fails closed on dirty source in this initial clean-workspace slice (requires source.before.dirty=false; keep dirty_hash as provided target identity).

Read material bytes again at READY and reject drift. The snapshot constructor receives validated `bridgeContext`, adds `techHub: binding` and `bridge: {registrationHash, materialInventory, runtimeAttestation:'NOT_ESTABLISHED', capabilityReadiness:...}` at its initial write. Keep existing source/observer drift checks. Do not require the new field for legacy runs or alter old snapshots. The existence of the hook does not expose a new CLI action or assert actual experiment execution.

### Arena/action foundation (contract-only)

Arena exact fields: `schemaVersion:1, arenaId, arenaEpoch, arenaRevision, baselineHash, bounds:{min:[x,y,z],max:[x,y,z]}, allowedMutationBounds, resetClasses`. Both bounds have integer coordinates, 0 < max-min <= 64 on each axis, height [-64,320], half-open containment min <= position < max; mutation bounds contained in Arena. `resetClasses` maps named supported classes to RESETTABLE/PERSISTENT_BY_DESIGN/EXTERNAL/UNKNOWN; initially allow blocks, block_entities, entities, effects, target_state, scheduled_ticks, game_rules, time_weather, chunk_tickets, probe_state.

Action envelope exact fields: `schemaVersion:1, debugSessionId,runId,runSnapshotId,processEpoch,arenaId,arenaEpoch,expectedArenaRevision,experimentId,actionId,idempotencyKey,type,args`. Supported detached intent types align with TECH HUB's first contract: wait_ticks, teleport_subject, set_block, use_item. No raw commands. Each requires a dedicated bounded args validator; `use_item` remains a validated intent with backend unavailable, never executable. Live capability list advertises no mutation actions until Java backends exist. Exact args: wait_ticks {ticks:1..1200}; teleport_subject {subject_id,position,rotation:[yaw:-180..180,pitch:-90..90]}; use_item {subject_id,hand:main_hand|off_hand,ticks:1..20}; set_block {position:integer[3],block:resourceId}. Subjects are an identity-context map of stable subject_id to canonical UUID; no guessed adapter names.

`validateResetEvidence` validates reported identity, before/after epoch/revision, expected/measured baseline hashes, changed/remaining state classes and evidence references. Output is `{valid, classification, scope:'CONTRACT_ONLY'}`; mismatched hash -> ARENA_NOT_CLEAN, missing/uncontrolled class -> INCONCLUSIVE. It neither resets nor declares a real Arena clean.

Journal is local per-run control data, not an evidence DB. Persist request payload digest before acceptance under `control/actions/<sha256(idempotencyKey)>/`. Immutable ordered receipt files, written with exclusive creation; serialized in-process writer plus filesystem exclusive reservation. Same key/payload returns existing outcome; different payload -> IDEMPOTENCY_CONFLICT. Allowed lifecycle: REQUESTED -> ACCEPTED -> APPLIED -> VERIFIED, with FAILED/NOT_RUN/PARTIAL_APPLY/OUTCOME_UNKNOWN terminal alternatives where applicable. Recovery of accepted/applied without terminal proof yields OUTCOME_UNKNOWN and forbids dispatch. No mutation function or command is executed by these APIs. `recordActionOutcome` is an internal backend seam, not request/CLI controllable; VERIFIED remains a reported receipt until a real typed backend supplies postcondition evidence.

### Stop verification

`verifyProcessesExited(records, {inspect, now, sleep, timeoutMs=5000,pollMs=50})` accepts recorded PID/start-time/command identities and returns `{status:'VERIFIED_EXIT'|'EXIT_TIMEOUT'|'OWNERSHIP_CHANGED'|'INSPECTION_UNKNOWN', observations, elapsedMs}`. Invalid/unbounded timing arguments fail. A missing process with no inspection error is exit; inspection failure is unknown; an existing PID whose start-time/command changed is ownership changed and must never be killed again. No new kill API is added.

`stopCurrent` retains existing run-bound flush and owned-process termination, then bounded verification. Only VERIFIED_EXIT writes STOPPED/live:false/ok:true. Otherwise preserve truthful status, ok:false and cleanup evidence. `readCurrent` must not erase uncertainty merely because inspectProcess reports exists:false with inspectionError. Finalization can record partial evidence but cannot bypass a currently live/unknown runtime gate through the bridge path. G1 acceptance safeStopPassed follows verified cleanup, not attempted kill.

## Task 1: Registration and material proof

- [ ] Write `registration.test.mjs` fixtures with UTF-8, 1.0, exponent values and -0.0; exact Python-style request/assertions bytes must retain expected known hashes, while any single-byte change fails
- [ ] Add tests for wrong binding fields/target hashes, duplicate JSON keys, malformed UTF-8, nonfinite/unsafe numbers, symlink/traversal/oversized/nonregular input, missing/replaced material and incomplete/conflicting registration
- [ ] Run `node --test debug-workspace/bridge/tests/registration.test.mjs`; require red failures for missing implementation
- [ ] Implement registration.mjs/materials.mjs contracts above using builtin APIs; verify no launch/import side effect and registry writes confined to runtimeRoot
- [ ] Re-run same test command; require all tests pass; inspect changed-file diff
- [ ] Record source-only evidence; commit only if a genuine exact-base Git checkout is later available, otherwise preserve reviewed patch

## Task 2: Initial immutable snapshot binding

- [ ] Add tests for initial techHub binding, exact unchanged legacy snapshot shape, material drift during startup, registration tampering, dirty source refusal and attempted posthoc duplicate snapshot write
- [ ] Run `node --test debug-workspace/bridge/tests/stop-snapshot.test.mjs`; require binding tests red
- [ ] Extract only the existing snapshot-object assembly into a pure exported `buildRunSnapshot(input)` helper in core.mjs, retaining writeImmutableRunSnapshot; add optional trusted registration resolution and pre/READY material verification
- [ ] Verify loaded runtime remains NOT_ESTABLISHED even when disk hashes match; no new CLI launch option or full readiness promotion
- [ ] Re-run new test file, then `node debug-workspace/selftest.mjs` (fake target only); require passing source tests and no legacy protocol regression
- [ ] Review/save diff

## Task 3: Detached Arena and durable action journal

- [ ] Read completed TECH HUB experiment_contract.py and freeze exact args schemas in plan before implementation; reject unsupported/extra fields, never silently map differently named actions
- [ ] Add `arena-journal.test.mjs` tests for bounds, finite numeric constraints, outside-region rejection, wrong UUID/run/snapshot/epoch/revision, unknown reset classes, mismatched baseline and unimplemented runtime capability
- [ ] Add concurrent same-key reservation tests, different-payload conflict, crash after ACCEPTED/APPLIED, torn/missing receipt, immutable terminal receipt and forbidden transition tests
- [ ] Run `node --test debug-workspace/bridge/tests/arena-journal.test.mjs`; require red failures
- [ ] Implement the two contract/journal modules with no world mutation; tests use fake internal receipt evidence only and label CONTRACT_ONLY
- [ ] Re-run same file; require all pass and no side effect outside test directory; review/save diff

## Task 4: Verified stop and honest coherence

- [ ] Add pure injected-process tests: immediate exit, eventual exit, timeout still live, inspection error, PID reuse, wrong command, partial launcher/runtime stop and invalid timeout bounds
- [ ] Add tests that stopCurrent/G1 acceptance cannot report success after failed exit verification; retain prior evidence-shutdown state separately
- [ ] Add Broker tests: supported LATEST_PER_LANE/BOUNDED_SKEW/SAME_TICK_WHERE_AVAILABLE/BEST_EFFORT remain valid, ATOMIC_SNAPSHOT/arbitrary mode rejects
- [ ] Run `node --test debug-workspace/bridge/tests/stop-snapshot.test.mjs` and `node debug-workspace/evidence/selftest.mjs`; require new red cases
- [ ] Implement process-stop helper and minimal core/finalize/broker changes; avoid unrelated supervisor refactor
- [ ] Re-run focused tests plus fake Supervisor selftest and G2 acceptance selftest; require passing source tests, preserve NOT_ESTABLISHED for runtime proof
- [ ] Review/save diff

## Task 5: Aggregate source verification and next-stage handoff

- [ ] Add `test:bridge-foundation` = `node --test debug-workspace/bridge/tests/registration.test.mjs debug-workspace/bridge/tests/arena-journal.test.mjs debug-workspace/bridge/tests/stop-snapshot.test.mjs`; document APIs are internal/source-level and all execution capabilities remain BLOCKED
- [ ] Run `npm run test:bridge-foundation`, `npm run test:debug-workspace`, `npm run test:g2-evidence`; save logs with exact baseline and changed file hashes
- [ ] Request independent review of contract/bounds/idempotency/cleanup seams; resolve findings with red/green tests
- [ ] Prepare exact diff and API inventory for authorized publication; no claim of full-repository npm test or Forge compilation without an authorized configured Forge build workspace
- [ ] Next separate plan: Java typed control inbox/receipt writer tied to identity and server thread; baseline/reset backend; epoch propagation; only then explicit camera barrier and human-state restoration. Each needs a Forge compile owner workspace and separate real-run authorization

## Self-review / scope boundary

This plan implements the smallest owner foundation, not the whole bridge design. Identity registration, local material integrity, durable intent/receipt semantics and verified-stop source behavior have concrete tests. JVM loaded-artifact proof, dirty-worktree cross-language fingerprint, real Arena reset, backend use_item behavior, camera barrier, images, dual presentation, visual-format benchmark and a real repair cycle intentionally remain unavailable. The action-args task is blocked until the adjacent TECH HUB schema is actually present; other tasks are independent and may proceed after parent review.

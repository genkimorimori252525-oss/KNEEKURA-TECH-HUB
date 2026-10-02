# Experimental runtime bridge contracts

Status: **X0/X1 CONTRACTS IMPLEMENTED; SCOPED LAB SOURCE CONNECTION AVAILABLE; LIVE ACCEPTANCE DEFERRED.**

The [phase-by-phase source record](POST-COMPLETION-SOURCE-2026-10-01.md) separates implemented code from deferred acceptance. The current optional control/import surface is documented in [LAB-SCOPED-CONTROL.md](LAB-SCOPED-CONTROL.md). It preserves these contracts and adds a separately pinned local adapter. Full runtime readiness and loaded-target attestation remain unestablished.

This starts the [approved successor design](../../../docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md).
It does not reopen or replace the accepted original MOD-AI/AI Usability Layer.
The [initial LAB audit](LAB-BRIDGE-READINESS-2026-10-01.md) records the starting prerequisites; the scoped-control document records the subsequent source connection.

## What is available

The explicit `experiment` CLI supports:

- `validate --request FILE`: pure bounded schema validation; no Store writes
- `prepare --request FILE`: freeze validated request, assertions and cross-repository binding in the existing Store
- `inspect-request --request-hash SHA256`: read an existing exact request
- `import-result --request-hash SHA256 --result FILE`: check and retain a report whose evidence blobs already exist in the Store
- `inspect-result --result-hash SHA256 [--current-target FILE]`: inspect immutable reported outcomes and mark changed dependencies `REVERIFY_REQUIRED`
- `compare --before FILE --after FILE [--changed-target FIELD]`: compare declared setup/assertions and explicitly permitted repair target changes

Use the existing global `--store` option. These offline operations do not launch a process. The separate scoped-control backend invokes only the pinned local Node adapter with a fixed command; it has no generic `execute`, runtime launch, network transport, auto-retry, scheduler or second database. TaskContext inspects explicit registrations and retained receipts without executing them. Readiness remains blocked by the unverified loaded runtime and real repair acceptance; default operation without an explicit registry stays unavailable.

## Request v1

Exact top-level fields:

`schema_version`, `experiment_id`, `generation`, `target`, `arena`, `subjects`,
`initial_state`, `actions`, `observation_scopes`, `visual_rig`, `assertions`, `budgets`.

- Target: exact profile/index/build/source/dirty/config/resource identities; preparation requires an existing complete Forge 47.x / Minecraft 1.20.1 / Java 17 ANCHOR profile and matching index/source identities
- Arena: registered ID/preset/baseline hash and integer half-open bounds, at most 64 blocks per edge, Y within −64..320
- Subjects: at most 16 stable subject IDs, unique exact UUIDs and entity resource IDs
- Typed actions: `wait_ticks`, `teleport_subject`, `use_item`, `set_block`; no raw commands, scripts, executable paths or embedded launch authority
- Initial state and actions share at most 32 unique action IDs; spatial actions remain inside declared bounds
- Observation: at most 16 exact-subject scopes with fixed allowed lanes and L0–L4 level
- Visual rig: `none` or `cardinal-4-snapshot-v1`, FOV 30..100, integer viewport 64..2048; the latter selects LAB's bounded four-view source implementation; real capture acceptance is still deferred
- Assertions: at most 32 stable IDs; explicit bounded structured fields/operators or fixed visual checks; no unconstrained aesthetic oracle
- Budgets: at most 120000ms, 32 actions and 16 captures; four-view requests need at least four captures

Preparation retains exact canonical request/assertion bytes in Store. LAB must
hash those received bytes, rather than reserialize numbers using a different
language's JSON conventions. Changing accepted assertions creates a different
request hash; repair comparison requires a newer generation whenever request
bytes differ. Execution idempotency is separately owned by LAB.

## Report import is not runtime attestation

An imported report always retains:

- `provenance: IMPORTED_LAB_REPORT`
- `runtime_attestation: NOT_ESTABLISHED`
- separate reported execution, cleanup and assertion outcomes

Matching JSON/hashes proves content identity and internal linkage. It cannot
prove that a JVM loaded those bytes, an Arena reset occurred, or an assertion
was observed. The registered LAB owner source path separately checks bounded diagnostic authority; real runtime acceptance must still establish those facts.
An imported `PASS` remains a reported result; it is never automatically promoted
to canonical truth or current runtime readiness.

Every referenced artifact is hash-verified with a bounded read before import.
The exact raw LAB RunSnapshot file content hash is distinct from LAB's logical
`snapshotHash`. The latter is retained with verification `NOT_ESTABLISHED`; this
Python importer does not silently substitute a different JSON canonicalizer.
The prelaunch `techHub` binding must exactly match the request, target, Arena
baseline and fixed assertions. Historical snapshots are never amended.

Raw scene, human composite, derived visual, structured, timeline, action and
finding evidence have distinct kinds. A definitive structured assertion needs
structured/timeline evidence; a visual assertion needs raw-scene/visual-bundle
evidence. A hash inventory alone does not assess that evidence's truth.

UNKNOWN/NOT_RUN/NOT_TRACKED/NOT_RENDERED/NOT_LOADED/INCONCLUSIVE stay distinct.
Uncertain execution or cleanup cannot carry a definitive behavior result.
Unknown completion selects read-only reconciliation; it never recommends retry.

## Comparison boundary

`compare` checks declared experiment semantics only. Arena baseline, subjects,
actions, scopes, assertions, budgets and rig must match. Changed target fields
must be individually declared, and their exact set must equal the real changes.
Before/after request hashes and generations remain explicit.

A `COMPARABLE` request pair still has `verification: NOT_RUN`. Actual frame
camera/frustum/viewport/state-window matching and the real repair experiment
remain X3/X6/X7 acceptance. A pixel difference is never an improvement verdict.

## Remaining gates

LAB owns the source implementations for bounded Arena/actions, camera capture/restoration, visual compilation, triggers, matched comparison and finalized evidence export. The optional native owner checks actual class-resource/container and disposable-world correspondence, while explicitly leaving loaded config/resources, transformed classes and full target attestation unestablished. Real reset/capture/restore acceptance, the visual-format benchmark, actual repair/resume cycle and Windows runtime gate remain deferred. X4/X6 final independent review is also unperformed because that review continuation was blocked; passing author tests do not replace it. X8 remains conditional and DEFERRED until a concrete same-frame requirement is observed.

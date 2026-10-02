# Unified Minecraft MOD-AI implementation plan

> **For agentic workers:** Use superpowers:executing-plans task by task; retain exact evidence and resume at the first unchecked item.

**Goal:** Join existing MOD-AI research/execution with the selected Blockbench asset backend and actual client verification, without duplicating the core or host AI.
**Architecture:** The existing coding AI uses thin adapters under `minecraft/`; the existing CAS binds specifications, artifacts, run receipts and observations. Application work remains in `departments/minecraft/mod-ai/`.
**Tech Stack:** Existing Python 3.11+, standard library for the first slice; target Minecraft 1.20.1, Forge exact profile version, game Java 17; externally managed Blockbench/sosadly.
**Spec:** `departments/minecraft/mod-ai/ASSET-INTEGRATION.md`, supplementing existing design v1.4 and the Foundation Session Record.

**Terminal status (2026-09-30): COMPLETE_SCOPED_CURRENT_PLAN.** The authorized
Linux/X11 staff pilot and bounded original U01–U06/A01–A24 criteria are complete.
See the [criterion reconciliation](../../../departments/minecraft/mod-ai/CURRENT-ACCEPTANCE-2026-09-30.md)
and [separate V6/V7 live evidence](../../../departments/minecraft/mod-ai/STAFF-LIVE-ACCEPTANCE-2026-09-30.md).
Windows remains conditional/unsupported, performance unmeasured, canonical
promotion excluded and positive Connector beta.50 compatibility unclaimed.
This status does not claim arbitrary-MOD or whole-platform acceptance.

## Global constraints

- Baseline PR #73 head `89cb81f412dd91df64785940569028e1a8be9920`; preserve #71/#72/#73 and main. A child branch is an additive continuation, not a merge.
- No independent Mod Agent, scheduler, DB, IDE or duplicate `labs/` tree. Reuse Store, Profile, execution, contracts, Observer, oracle and history.
- `sosadly/blockbench-mcp` selected at `028cdd76589de2e2cea51bfd79495b50a3c7d1d2`; Vibecraft is reference-only until actual code compatibility is demonstrated.
- No silent Forge upgrade; no canonical promotion; no script/plugin install by default; no production world; no auto-launch on read; no blind mutation retries.
- Preserve prior 597-test/Forge evidence at its tested revision. New local fixture tests are not that full suite or live desktop acceptance.
- Latest #73 status allows standard GitHub-hosted CI, superseding the old CI-off note. No home runner while public; do not change visibility or runner configuration. This slice does not dispatch CI.
- Original real providers/Core caller/U01-U06/A01-A24/Windows/client acceptance stay outstanding until specifically evidenced.

## Review focus

1. Specs cannot smuggle a destination, URL, script or authority; reject unknown fields, unsafe portable resource IDs and duplicate JSON keys.
2. Old/partial/edited profiles cannot masquerade as the target; verify canonical identity and exact target values before CAS mutation.
3. A loopback response is not authenticated plugin provenance; surface loaded revision UNKNOWN and reject protocol/ID ambiguity.
4. Redirects, oversized/truncated/slow responses and malformed JSON must not hang, retry, execute or turn into PASS.
5. A simulated bridge/test stub is not Blockbench; retain fixture/live labels and separate structure/visual/runtime verdicts.

## Ordered integration roadmap

### M0 — Reconcile and retain (documentation)
- [x] Read #73 and existing source/status/design; preserve all completed server work.
- [x] Pin and inspect upstream transport; correct the unsupported Vibecraft drop-in assumption.
- [x] Record one application home and the dependency order below.

### M1 — Asset request and read-only provider preflight (first implementation slice)
Files: create `minecraft/asset_contract.py`, `minecraft/blockbench.py`, `minecraft/assets.py`; tests `test_minecraft_asset_contract.py`, `test_minecraft_blockbench.py`, `test_minecraft_assets_cli.py`; examples/docs under `mod-ai/assets/`.
Consumes: existing `storage.Store`, `capture_profile`, `canonical`, `key_for`, `ContractError`.
Produces: `validate_spec(value: dict) -> dict`, `prepare_request(store: Store, *, profile: dict, spec: dict, index_id: str | None = None) -> dict`, `probe(store: Store, registry: dict) -> dict`.
- [x] Write and run RED tests for strict specs, immutable profile/style binding, inert hostile text, bad IDs/unknown keys, missing references, and no side effects on invalid input.
- [x] Implement the contract; run GREEN plus unchanged storage regression tests.
- [x] Write and run RED protocol tests using a real local HTTP fixture: allowlist, permission-off, request IDs, protocol/type mismatch, bounded payloads, redirects, timeout and no automatic retry.
- [x] Implement a read-only bridge probe with a total deadline per request, observations in the existing CAS, explicit unverified loaded revision, and NOT_RUN quality gates. Run GREEN.
- [x] Write and run RED subprocess CLI tests; implement check/prepare/probe with JSON results and meaningful exit codes. No dependencies or global settings installed.
- [x] Self-audit, run all available selected-file tests and verify unchanged upstream blob IDs. See `departments/minecraft/mod-ai/assets/IMPLEMENTATION-2026-09-28.md` for exact evidence.

Publish changed files only against the exact remote parent; the enclosing PR records publication, not a local synthetic commit. The standard-hosted regression workflow is allowed to run automatically; no manual dispatch is made.

### M2 — Disposable Blockbench writer and export
Consumes: M1 request/spec/style/profile IDs and pinned provider selection.
Produces: immutable AssetArtifact inventory with native source/export/reference hashes and bounded AssetObservation records.
- [x] Locate exact upstream commands and prove exclusive project identity, no script/plugin operations, path scope and overwrite protections; refuse mutation until those guards actually exist.
- [x] Test ambiguous completion and wrong-project cases before adding allowlisted model/texture calls. Never retry an uncertain write.
- [x] Generate ONE Celestial Staff in a disposable local editor project. Render required views; host AI reviews, repairs and records evidence, without accepting an upstream numeric score as truth.
- [x] Export Java item JSON + PNG + native bbmodel; verify geometry/texture references, UV/display constraints and captured byte hashes. Live Blockbench acceptance is distinct from protocol fixtures.

### M3 — Existing research adapter acceptance and Forge integration
Can prepare provider/Core fixtures during M2; required before complete-product acceptance, not a reason to block static item planning on all upstream research.
Consumes: M2 captured artifacts, existing external providers/Core bridge and ProjectProfile.
Produces: actual provider/Core evidence and same-generation Forge compile/packaging receipt.
- [x] Exercise existing Vineflower/tiny-remapper with explicit real pinned tool/JDK/mapping inputs; mark each unsupported/unrun capability accurately. Do not build replacements.
- [x] Exercise the existing new Core caller with real schemas/research records; retain human canonical gates.
- [x] Import staff into a registered disposable Forge 1.20.1 MOD workspace without overwrites; re-capture inputs after code/assets change and use existing build/export/contract preparation.
- [x] Verify packaged resource IDs and same-source receipts. Implement a small right-click ability with predeclared expectations using the existing coding AI, not a new agent service.

M3 progress detail: the unchanged pinned providers ran on actual staff-MOD
classes, all 101 exact Forge classpath artifacts and official-input-derived
mappings; decompiled output recompiled and remapped instructions matched a
same-source ForgeGradle output. Core staged actual staff source records while
preserving human canonical gates. Deployed Core and upstream Twilight/Connector
acceptance are not inferred. The staff build/package and authenticated handler
GameTests retain their exact separate generation hashes.

### M4 — Client observation and verified input
Consumes: M3 build/run contract and existing `forge-observer/ClientProbe.java`.
Produces: same-run screenshot/state/log/input evidence, not a second runtime authority.
- [x] Prove existing client capture on the target environment before creating more screenshot infrastructure.
- [x] Select the smallest verified input driver; Vibecraft and langyo are research inputs, not accepted dependencies. Source/API and Forge1.20.1/Java17 fit are verified for Linux/X11; Windows fit remains explicitly unsupported and conditional.
- [x] Require foreground target identity, scoped coordinates, key release, run/epoch correspondence and bounded operations. Keep actual right-click distinct from test commands.
- [x] Observe inventory/first-person/third-person display and actual use; evaluate server state, visuals and synchronization separately. V6 supplies scoped behavior/control evidence; V7 supplies third-person held staff and active Glowing visibility. Performance is unproven without a dedicated measurement.

M4 progress detail: a concrete Linux/X11 right-button backend, authenticated
process-start/window binding, session-owned replay/quarantine ledger, screenshot/
log evidence route and explicit client save layout are implemented and fixture
tested. The observer compiles against actual Forge/Java17. A bounded live Linux
client pilot now verifies authenticated input/capture, Glowing/cooldown and
inventory/first-person views. That historical third-person view was occluded. The subsequent continuation
implements dedicated receiving-client contracts, independent state/packet
evidence, fixed control/repeat/expiry checks and a scoped integrated Hydra route;
its bounded V6/V7 live results are recorded separately with exact run identities.
The historical occlusion and timeout outcomes remain unchanged. Windows input is
unsupported, not silently treated as covered by Linux. Native/X server failure can leave release UNKNOWN and is
quarantined rather than retried.

### M5 — One real MOD editing cycle and final acceptance
- [x] Author pinned U01–U06 task inputs, A01–A24 fault recipes, fixed client/server assertions and negative controls without inventing execution results.
- [x] Execute investigate -> edit/assets -> build -> interact -> observe -> repair using fixed assertions and user launch budgets.
- [x] Exercise original U01-U06/A01-A24 plus the M1-M4 asset/input negatives at their declared layers; retain unrun broader prerequisites as NOT_RUN/BLOCKED and U06's supported UNKNOWN as a bounded investigation result.
- [x] Record failures/repairs through existing history. Preserve the research queue Twilight Forest -> Sinytra Connector; these investigations are not delegated to Vibecraft.
- [x] Close only the verified scope. Stop speculative feature growth; add future features only for a demonstrated failure or missing necessary task.

## Current verified continuation — 2026-09-30

This current plan is complete in the declared scope. The
[deferred improvements](../../../departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md)
remain separate follow-on work; no proposed feature is implemented by this closure.
The [current criterion reconciliation](../../../departments/minecraft/mod-ai/CURRENT-ACCEPTANCE-2026-09-30.md)
separates verified Linux staff/U/A results from conditional platform and broader
acceptance limits. The historical
[bounded runtime batch](../../../departments/minecraft/mod-ai/RUNTIME-BATCH-2026-09-30.md)
preserves earlier preflight/startup failures, limits and cleanup outcomes.

See `departments/minecraft/mod-ai/CONTINUATION-2026-09-30.md` for current
implementation, real Blockbench/editor review/export evidence, Core/provider
acceptance boundaries, and exact-head verification. The old native-capture RED
and selected-file-only environment described below are historical.

## Historical local-agent handoff checkpoint — 2026-09-28

The historical detailed resume state is recorded in
`departments/minecraft/mod-ai/LOCAL-AI-HANDOFF-2026-09-28.md`.

The executable-code head reviewed at that checkpoint was
`824a2365a0ac945620f26a15339b352ac0de35f6`. Its hosted run
`36398566854` was intentionally/actually RED at that TDD boundary:
787 passed, 2 failed, with the remaining failures both pointing to the same missing
pathless native `.bbmodel` capture contract. That resolved RED remains historical;
use the terminal reconciliation above rather than restarting this old boundary.

## Historical execution conditions (superseded by continuation)

Durable list_workflows returned an MCP 404; no duplicate workflow was created.
Direct container git clone failed DNS, and archive retrieval was unavailable.
Use a selected-file local checkout with Git blob verification for tests and GitHub
Git object APIs for an additive child branch. No full-checkout, PostgreSQL, live
Blockbench/Minecraft, or Windows result may be claimed from this local environment.
No independent reviewer/subagent is available; identify the review as author self-review.

Final continuation: [recovery acceptance](../../../departments/minecraft/mod-ai/RECOVERY-ACCEPTANCE-2026-09-30.md)
satisfies default/no-JAPPA U04 rendering; [staff V6/V7 acceptance](../../../departments/minecraft/mod-ai/STAFF-LIVE-ACCEPTANCE-2026-09-30.md)
closes the declared M4/M5 staff scope. Follow-on usability work is a separate
stage and has not been implemented by this closure.

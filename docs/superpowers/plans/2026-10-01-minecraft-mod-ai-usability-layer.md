# Minecraft MOD-AI Usability Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a thin, read-only-by-default AI task context and readiness facade over the existing Minecraft MOD-AI adapters so a coding agent can see the exact target, available evidence, blockers, and a few valid next operations without learning the entire internal command graph.

**Architecture:** Keep all authority and execution in the existing Store/Profile/index/registry/session/Observer/asset/runtime modules. Add one compact context module for validated task inputs and lineage, one routing module for readiness and next-operation derivation, and a narrow `task` CLI namespace. Do not add a scheduler, persistent task state, autonomous planner, database, or MCP business layer; MCP remains a separate decision after the real usability trial.

**Tech Stack:** Python 3.11+, standard library, existing `kneekura_tech_hub.minecraft` modules and Store/CAS, pytest, existing JSON CLI.

**Spec:** `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-usability-layer-design.md`

## Global Constraints

- **Completion gate:** do not start implementation until the current unified MOD-AI plan is closed for the user-approved scope, or the user explicitly closes/defer-resolves its remaining acceptance gates and authorizes this follow-on.
- Reuse the existing Store/CAS, ProjectProfile/index, execution registries, runtime sessions, receipts, asset interfaces, Observer, GameTest and Core governance boundaries.
- `task prepare` and `task capabilities` are read-only derivations: no Gradle/provider execution, network access, Minecraft/Blockbench launch, world mutation, native input, launch-budget consumption, or Core/canonical write.
- Task free text is inert data and never grants paths, executables, providers, scripts, plugin installation, launches, native input or canonical authority.
- No new database, scheduler, workflow engine, autonomous agent service, vector DB, canonical graph, or duplicate run manager.
- Preserve separate ANCHOR / FRONTIER / COMPARATIVE identities; never infer one track from another.
- Preserve UNKNOWN / PARTIAL / BLOCKED / UNSUPPORTED. An UNKNOWN prior mutation must never produce a replay/retry recommendation.
- Default compact response: at most **12 capability entries** and **5 next actions**; never inline large source, bytecode, log, image or artifact bodies.
- Existing top-level `capabilities` remains static surface discovery; task-scoped readiness is a separate contract.
- Initial implementation has **no `task run`** and no MCP server. Existing low-level routes continue to own mutations.
- Session secrets, authentication tokens and private machine paths must not appear in public TaskContext output.

## Review Focus

1. **Hostile task text containing commands, paths or permission language** — it must remain inert and must not alter registries, authorities or next-action parameters. Covered in Task 1.
2. **Stale/mismatched index, session, registry or evidence identities** — capability readiness must fail closed rather than present READY. Covered in Tasks 1–3.
3. **Prior UNKNOWN write/input/run receipt** — routing must surface reconciliation and omit replay/retry of the uncertain mutation. Covered in Task 4.
4. **Secret-bearing local session input** — TaskContext must never emit token, endpoint path, session path, world path, build path or other private authority material. Covered in Tasks 1–2 and CLI Task 5.
5. **Huge index/history/evidence inputs** — compact output size must stay bounded and proportional to pointers/counts, not evidence body size. Covered in Tasks 2 and 4.

---

## File Structure

Create:

- `src/kneekura_tech_hub/minecraft/task_context.py` — strict TaskRequest validation, authoritative read-only input loading, compact target/evidence/lineage summaries, final TaskContext assembly.
- `src/kneekura_tech_hub/minecraft/task_routing.py` — capability readiness evaluation and bounded next-action derivation only.
- `tests/test_minecraft_task_context.py` — request/input/target/evidence/lineage/bounds/security tests.
- `tests/test_minecraft_task_routing.py` — readiness/reason/next-action tests.
- `departments/minecraft/mod-ai/TASK-CONTEXT.md` — AI/operator contract and happy-path usage.

Modify:

- `src/kneekura_tech_hub/minecraft/connected_cli.py` — register and dispatch `task prepare` / `task capabilities`; label existing top-level capabilities as static surface.
- `tests/test_minecraft_connected_cli.py` — CLI parser/dispatch/parity/no-side-effect coverage.
- `tests/test_minecraft_cli.py` — subprocess JSON/exit/help coverage if required by existing test organization.
- `departments/minecraft/mod-ai/README.md` — link the task facade after implementation.
- `departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md` — mark its state/lineage presentation concerns as implemented only after acceptance; leave asset-editing Candidates 1–3 deferred.

Do not restructure unrelated existing modules.

---

### Task 1: Strict TaskRequest and authoritative read-only input normalization

**Files:**
- Create: `src/kneekura_tech_hub/minecraft/task_context.py`
- Create: `tests/test_minecraft_task_context.py`

**Interfaces:**
- Consumes: `Store`, `index._load(store, index_id)`, `verification._identity_errors(...)`, `canonical(...)`, `key_for(...)`, `valid_hash(...)`.
- Produces:
  - `validate_task_request(value: dict) -> dict`
  - `load_task_inputs(store: Store, *, index_id: str | None = None, run_registry: dict | None = None, input_registry: dict | None = None, blockbench_registry: dict | None = None, session: dict | None = None, evidence_hashes: tuple[str, ...] = (), world: str | None = None, run_directory: str | None = None) -> dict`

- [ ] **Step 1: Write failing TaskRequest contract tests**

Test these exact rules:

```python
def test_task_request_is_strict_bounded_inert_json():
    request = {
        "schema_version": 1,
        "intent": "edit_code",
        "goal": "Add homing danmaku to Reimu",
        "constraints": ["Keep Forge 1.20.1"],
        "acceptance": ["Projectile visibly homes on the declared target"],
    }
    assert validate_task_request(request) == request

def test_task_request_rejects_authority_fields_and_unknown_keys():
    # path, command, executable, registry, provider, script, permission,
    # launch and plugin fields are not part of the exact five-field contract.
    ...

def test_task_request_text_is_inert_even_when_it_contains_shell_or_prompt_instructions():
    ...
```

Pin these values:

- exact fields: `schema_version`, `intent`, `goal`, `constraints`, `acceptance`;
- schema version exactly integer `1`;
- intents exactly: `investigate`, `edit_code`, `create_asset`, `verify_server`, `verify_client`, `compatibility_research`;
- `goal`: nonempty string, max 4096 Unicode code points;
- `constraints` and `acceptance`: arrays of at most 32 nonempty strings, each max 1024 code points;
- finite canonical JSON only.

- [ ] **Step 2: Run TaskRequest tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py -k "task_request"`

Expected: FAIL because `task_context` / `validate_task_request` does not exist.

- [ ] **Step 3: Implement `validate_task_request(value: dict) -> dict`**

Detach with existing canonical JSON rules. Do not interpret strings, expand environment variables, normalize paths, parse commands, or derive authority from text.

- [ ] **Step 4: Run TaskRequest tests and verify GREEN**

Run the same focused command.

Expected: all selected tests PASS.

- [ ] **Step 5: Write failing input-normalization tests**

Cover:

- valid index ID loads only the immutable existing index;
- index/profile identity mismatch or wrong artifact type is rejected;
- evidence hash list is at most 32 distinct lowercase SHA-256 IDs;
- duplicate evidence IDs are rejected;
- malformed registry JSON is detached but never executed;
- supplied session contract with `verification._identity_errors` failures is rejected;
- input loading does not change `Store.pinned_hashes()` or create blobs;
- hostile request text does not alter any normalized registry/session/evidence field.

Session input in module tests is already-loaded JSON. The CLI later uses `runtime.load_session` to enforce the existing private-file rules.

- [ ] **Step 6: Run input-normalization tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py -k "inputs or index or evidence"`

Expected: FAIL because `load_task_inputs` is missing.

- [ ] **Step 7: Implement `load_task_inputs(...)`**

Requirements:

- use `index._load` for `index_id`;
- do not repair or prepare an index;
- canonical-detach optional registries;
- validate the supplied session's existing contract identity without contacting its endpoint;
- validate evidence hashes and existence with bounded metadata inspection only;
- retain raw registry/session objects only inside the returned internal input bundle; public summaries are produced later;
- never write Store/CAS;
- no process/network APIs.

- [ ] **Step 8: Run the whole Task 1 test file**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/kneekura_tech_hub/minecraft/task_context.py tests/test_minecraft_task_context.py
git commit -m "feat: add strict Minecraft task context inputs"
```

---

### Task 2: Compact target, evidence and lineage summaries with secret redaction

**Files:**
- Modify: `src/kneekura_tech_hub/minecraft/task_context.py`
- Modify: `tests/test_minecraft_task_context.py`

**Interfaces:**
- Consumes: Task 1's normalized input bundle.
- Produces:
  - `summarize_target(inputs: dict) -> dict`
  - `summarize_evidence(store: Store, inputs: dict) -> dict`
  - `summarize_lineage(inputs: dict, evidence: dict) -> list[dict]`

- [ ] **Step 1: Write failing target-summary tests**

For a valid index, assert exact target fields come from `snapshot["profile"]["manifest"]` / profile identity:

- `profile_id`
- `profile_hash`
- `index_snapshot_id`
- `minecraft`
- `loader`
- `loader_version`
- `java_major`
- `track`
- `workspace_revision`

When no index exists, these fields are null with explicit `unknown_fields`; do not synthesize Forge 1.20.1 merely from the TaskRequest intent.

- [ ] **Step 2: Run target tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py -k "target_summary"`

Expected: FAIL because `summarize_target` is missing.

- [ ] **Step 3: Implement `summarize_target(inputs: dict) -> dict`**

Use only captured index/profile values. Keep track identity explicit.

- [ ] **Step 4: Write failing evidence/lineage tests**

Use real-shaped small CAS records and assert:

- mapping record recognized by `kind == "mapping-table"`;
- Failure / Repair History recognized by `format == "kneekura.failure-history.v1"`;
- generic receipt pointers retain only bounded identity/status fields such as `kind`, `record_type`, `status`, `outcome`, `run_id`, `profile_id`, `index_snapshot_id`, `build_artifact_hash` when present;
- unknown/large/non-JSON evidence remains an opaque hash/size pointer, not an inlined body;
- lineage reuses existing IDs/hashes and does not create new Store objects;
- session token, `endpoint_path`, `report_path`, `directory`, `world`, `build_artifact`, absolute registry workspace paths and input display authority do not appear anywhere in serialized public summaries.

- [ ] **Step 5: Run evidence/lineage tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py -k "evidence or lineage or secret"`

Expected: FAIL because summary functions are missing.

- [ ] **Step 6: Implement evidence and lineage summaries**

Bounded rules:

- at most 32 evidence pointers;
- do not parse evidence records larger than 1 MiB; report hash + byte size only;
- never include source/log/image/body fields;
- keep lineage as a short ordered list of existing identity references, not a new persisted record;
- no Store writes/pins.

- [ ] **Step 7: Write and pass the context-size regression**

Construct an index with thousands of document metadata rows plus a 1 MiB opaque evidence blob. Assert the serialized target/evidence/lineage summary remains below **64 KiB** and does not contain document bodies or opaque payload bytes.

Run:

`python -m pytest -q tests/test_minecraft_task_context.py`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/kneekura_tech_hub/minecraft/task_context.py tests/test_minecraft_task_context.py
git commit -m "feat: summarize Minecraft task evidence and lineage"
```

---

### Task 3: Context-aware capability readiness evaluator

**Files:**
- Create: `src/kneekura_tech_hub/minecraft/task_routing.py`
- Create: `tests/test_minecraft_task_routing.py`

**Interfaces:**
- Consumes: Task 1 input bundle and Task 2 summaries; existing `verification.validation_plan(...)` for read-only registered-run planning where applicable.
- Produces:
  - `evaluate_capabilities(request: dict, inputs: dict, evidence: dict) -> list[dict]`
  - each capability record exactly: `{"id", "surface", "readiness", "reason_code", "missing", "evidence"}`

Capability IDs, in stable order:

1. `source_search`
2. `bytecode_inspect`
3. `mappings`
4. `failure_history`
5. `core_context`
6. `blockbench_asset`
7. `forge_build`
8. `gametest`
9. `server_observation`
10. `client_observation`
11. `native_input`

Allowed values:

- `surface`: `IMPLEMENTED` | `UNSUPPORTED`
- `readiness`: `READY` | `NOT_CONFIGURED` | `BLOCKED` | `UNKNOWN`

- [ ] **Step 1: Write the seven required routing-quality fixtures as failing tests**

Tests must include the spec's acceptance fixtures:

1. no index → source/bytecode not configured and environment capture prerequisite visible;
2. exact indexed Forge target → `source_search` READY;
3. create-asset request with no Blockbench registry → `blockbench_asset` NOT_CONFIGURED / `PROVIDER_NOT_REGISTERED`;
4. successful build receipt + registered prepared world/run inputs → `gametest` readiness follows read-only existing validation-plan checks;
5. supplied UNKNOWN input/run receipt → affected runtime/input capability UNKNOWN / `SESSION_UNKNOWN_COMPLETION`;
6. valid Linux client session + explicit enabled `linux-x11-send-event-v1` input registry → `native_input` may be READY only when all existing identity prerequisites are present;
7. Windows/client target with no supported backend → `native_input` readiness UNSUPPORTED / `WINDOWS_INPUT_UNSUPPORTED`, never READY.

Also cover mappings/history detection from Task 2 evidence pointers.

- [ ] **Step 2: Run capability tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_routing.py -k "capabilit"`

Expected: FAIL because `task_routing` is missing.

- [ ] **Step 3: Implement capability evaluation conservatively**

Rules:

- code surface existence and runtime readiness are separate;
- source readiness requires a valid supplied index;
- bytecode readiness is UNKNOWN if the index has no prepared bytecode or unresolved coverage prevents the requested certainty;
- mappings READY only with an explicitly supplied recognized mapping record;
- history READY only with a recognized captured history record;
- Core context is NOT_CONFIGURED when no Core configuration is present and UNKNOWN when configured but not probed; this read-only evaluator does not connect to PostgreSQL;
- Blockbench is NOT_CONFIGURED without an explicit Blockbench registry, UNKNOWN when registered but no retained readiness evidence establishes the guarded provider state;
- build/GameTest use existing read-only validation helpers rather than duplicating execution-policy rules;
- observation/input require existing session/registry identities and never contact a live endpoint;
- any inconsistent identity is BLOCKED or UNKNOWN, never silently downgraded to READY.

Use the design reason codes where applicable:
`PROFILE_MISSING`, `INDEX_STALE`, `MAPPING_NOT_CONFIGURED`,
`PROVIDER_NOT_REGISTERED`, `LAUNCH_NOT_AUTHORIZED`,
`SESSION_UNKNOWN_COMPLETION`, `WINDOWS_INPUT_UNSUPPORTED`,
`EVIDENCE_SCOPE_INSUFFICIENT`.

Add narrower codes only when a stable machine distinction is necessary; do not route by prose.

- [ ] **Step 4: Add a no-side-effect capability test**

Monkeypatch/block process spawn and network connection APIs used elsewhere. Snapshot Store pins/blobs and registry launch counters before/after. Run `evaluate_capabilities`; assert no blocked function was called and no state changed.

- [ ] **Step 5: Run Task 3 tests and full existing related regressions**

Run:

`python -m pytest -q tests/test_minecraft_task_routing.py tests/test_minecraft_connected_cli.py tests/test_minecraft_runtime.py tests/test_minecraft_input_route.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/kneekura_tech_hub/minecraft/task_routing.py tests/test_minecraft_task_routing.py
git commit -m "feat: derive Minecraft task capability readiness"
```

---

### Task 4: Bounded next-action router and complete TaskContext assembly

**Files:**
- Modify: `src/kneekura_tech_hub/minecraft/task_context.py`
- Modify: `src/kneekura_tech_hub/minecraft/task_routing.py`
- Modify: `tests/test_minecraft_task_context.py`
- Modify: `tests/test_minecraft_task_routing.py`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces:
  - `derive_next_actions(request: dict, inputs: dict, capabilities: list[dict]) -> list[dict]`
  - `prepare_task_context(store: Store, request: dict, *, index_id: str | None = None, run_registry: dict | None = None, input_registry: dict | None = None, blockbench_registry: dict | None = None, session: dict | None = None, evidence_hashes: tuple[str, ...] = (), world: str | None = None, run_directory: str | None = None) -> dict`

TaskContext top-level fields:

```text
schema_version
kind = "minecraft_task_context"
status
task
target
evidence
capabilities
next_actions
lineage
```

`task` contains only `request_hash` and `intent`; the host AI already has the goal text.

Each next-action record exactly contains:

```text
operation_id
primary
mode = READ_ONLY | SIDE_EFFECTING
authorization_required
reason_code
required_inputs
```

No shell command or path appears in an action.

- [ ] **Step 1: Write failing next-action tests**

Pin these cases:

- no index → `profile.resolve` is primary, SIDE_EFFECTING, authorization required;
- valid index for `investigate` / `edit_code` → `research.search` is a valid READ_ONLY action;
- recognized history → `history.query` may appear as a read-only alternative;
- `create_asset` with exact target but missing provider registry → `asset.prepare` may be offered, but no Blockbench mutation action;
- build/GameTest prerequisites proven → `gametest.prepare` may appear;
- UNKNOWN prior write/input/run evidence → `runtime.reconcile_unknown` is primary and no replay/retry action for that mutation is present;
- no more than 5 actions;
- equal alternatives may all be `primary: false`; the router must not invent a winner.

- [ ] **Step 2: Run next-action tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_routing.py -k "next_action or unknown"`

Expected: FAIL because `derive_next_actions` is missing.

- [ ] **Step 3: Implement `derive_next_actions(...)`**

Use a small explicit rule table over TaskRequest intent + capability readiness. Do not build a general workflow DSL or recursive planner.

No action may contain:

- executable argv;
- filesystem destination;
- provider URL;
- script/code;
- token;
- auto-retry flag.

- [ ] **Step 4: Write failing complete-context tests**

Assert:

- semantically identical inputs produce byte-identical canonical TaskContext;
- changing only TaskRequest goal text changes request hash but cannot change authority/readiness unless typed intent/authoritative inputs also change;
- all public sections are secret/path-redacted;
- capabilities <= 12 and next actions <= 5;
- whole canonical TaskContext <= **96 KiB** for the large-index fixture;
- no Store writes/pins;
- stale/mismatched evidence fails closed rather than disappearing silently.

- [ ] **Step 5: Run complete-context tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py -k "prepare_task_context or deterministic or bounded"`

Expected: FAIL because `prepare_task_context` is missing.

- [ ] **Step 6: Implement `prepare_task_context(...)`**

Compose only Tasks 1–4. Set top-level `status` to:

- `OK` when all supplied authoritative inputs are valid and at least one useful next action exists;
- `PARTIAL` when the task is valid but prerequisites are missing/unknown;
- fail with `ContractError` on stale/mismatched/corrupt authoritative inputs.

Do not persist TaskContext by default.

- [ ] **Step 7: Run Task 4 tests**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py tests/test_minecraft_task_routing.py`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/kneekura_tech_hub/minecraft/task_context.py src/kneekura_tech_hub/minecraft/task_routing.py tests/test_minecraft_task_context.py tests/test_minecraft_task_routing.py
git commit -m "feat: assemble bounded Minecraft AI task context"
```

---

### Task 5: Expose `task prepare` and `task capabilities` without adding an executor

**Files:**
- Modify: `src/kneekura_tech_hub/minecraft/connected_cli.py`
- Modify: `tests/test_minecraft_connected_cli.py`
- Modify: `tests/test_minecraft_cli.py` if subprocess coverage belongs there

**Interfaces:**
- Consumes: `prepare_task_context(...)`.
- Produces CLI:
  - `task prepare`
  - `task capabilities`
- Existing top-level `capabilities` gains `capability_scope: "STATIC_SURFACE"` while preserving its existing fields and operations list.

Both task subcommands accept:

```text
--request TASK_REQUEST_JSON
--index INDEX_SNAPSHOT_ID              (optional)
--run-registry RUN_REGISTRY_JSON       (optional)
--input-registry INPUT_REGISTRY_JSON   (optional)
--blockbench-registry REGISTRY_JSON    (optional)
--session PRIVATE_SESSION_JSON         (optional)
--evidence SHA256                      (repeatable, max 32)
--world OWNED_WORLD_PATH               (optional readiness input only)
--run-directory OWNED_RUN_DIR          (optional readiness input only)
```

- [ ] **Step 1: Write failing parser/help tests**

Assert:

- both task subcommands parse;
- there is no `task run`;
- existing top-level commands still parse;
- top-level static `capabilities` still exposes its prior operations list and now labels `capability_scope == "STATIC_SURFACE"`.

- [ ] **Step 2: Run parser tests and verify RED**

Run:

`python -m pytest -q tests/test_minecraft_connected_cli.py tests/test_minecraft_cli.py -k "task or capabilities"`

Expected: FAIL because task subcommands are not registered.

- [ ] **Step 3: Implement parser registration**

Use existing `read_json` for TaskRequest/registries and `runtime.load_session(args.session)` for the private session path. Do not put session contents into CLI output.

- [ ] **Step 4: Write failing dispatch/parity tests**

For one fixture, call `prepare_task_context(...)` directly and `connected_cli.dispatch` via parsed args. Assert normalized results match.

For `task capabilities`, return exactly:

```text
schema_version
status
target
capabilities
```

from the same prepared context; do not maintain a second evaluator.

Also assert:

- session token and private paths absent from serialized CLI JSON;
- malformed session permissions/identity fail through the existing `runtime.load_session` rules;
- task commands do not execute mocked Gradle/network/native-input functions;
- CLI exit remains nonzero for existing ERROR/STALE/UNSUPPORTED/BLOCKED/UNKNOWN semantics and does not invent special retry behavior.

- [ ] **Step 5: Run dispatch tests and verify RED**

Run the same focused test files.

Expected: FAIL until dispatch is wired.

- [ ] **Step 6: Implement task dispatch and static-capability label**

Keep `context` unchanged; it remains research/Core context. Do not alias TaskContext to it.

- [ ] **Step 7: Run CLI and related regression tests**

Run:

`python -m pytest -q tests/test_minecraft_connected_cli.py tests/test_minecraft_cli.py tests/test_minecraft_task_context.py tests/test_minecraft_task_routing.py`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/kneekura_tech_hub/minecraft/connected_cli.py tests/test_minecraft_connected_cli.py tests/test_minecraft_cli.py
git commit -m "feat: expose Minecraft AI task context CLI"
```

---

### Task 6: Document the AI happy path and close code acceptance

**Files:**
- Create: `departments/minecraft/mod-ai/TASK-CONTEXT.md`
- Modify: `departments/minecraft/mod-ai/README.md`
- Modify: `departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md`
- Test: existing task/CLI tests plus full repository suite

**Interfaces:**
- Consumes: stable CLI contract from Task 5.
- Produces: operator/AI documentation only; no new runtime authority.

- [ ] **Step 1: Write `TASK-CONTEXT.md`**

Document:

- purpose and read-only boundary;
- exact TaskRequest fields/intents;
- exact CLI flags;
- capability surface/readiness meanings;
- reason-code behavior;
- no-retry rule for UNKNOWN;
- compact-first / expand-with-existing-`search`/`inspect`/`artifact read` flow;
- code-edit, asset and compatibility-research happy-path examples;
- explicit statement that `task prepare` never executes a next action;
- MCP remains undecided.

Do not include real tokens/private machine paths.

- [ ] **Step 2: Link the README and deferred-improvement ownership**

README links to `TASK-CONTEXT.md`.

In `DEFERRED-IMPROVEMENTS-2026-09-30.md`, mark only the secondary state/next-action and artifact-lineage concerns as implemented by this layer **after** the tests below pass. Leave asset-editing Candidates 1–3 DEFERRED.

- [ ] **Step 3: Run the focused task facade suite**

Run:

`python -m pytest -q tests/test_minecraft_task_context.py tests/test_minecraft_task_routing.py tests/test_minecraft_connected_cli.py tests/test_minecraft_cli.py`

Expected: PASS.

- [ ] **Step 4: Run the complete repository suite**

Run the repository's normal full command:

`python -m pytest -q`

Expected: zero unexpected failures. Environment-dependent PostgreSQL/Java/desktop skips must be reported exactly rather than relabeled as pass.

- [ ] **Step 5: Run packaging/install regression if the current repository packaging suite does not already cover the new modules**

At minimum:

`python -m pytest -q tests/test_minecraft_packaging.py`

Expected: PASS and built/installable package contains `task_context.py` and `task_routing.py` when the packaging test exposes file inventory.

- [ ] **Step 6: Commit**

```bash
git add departments/minecraft/mod-ai/TASK-CONTEXT.md departments/minecraft/mod-ai/README.md departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md
git commit -m "docs: document Minecraft AI task context workflow"
```

---

## Post-implementation real AI usability acceptance gate

This is a product acceptance exercise, not another autonomous subsystem and not a reason to fabricate a universal score.

After Tasks 1–6 are green and the original MOD-AI completion gate has been satisfied:

- [ ] Pick one real MOD-making task with a fixed target and acceptance statement.
- [ ] Give the coding AI the TaskRequest plus only the explicit authoritative references it actually has.
- [ ] Start with `task prepare`; do not give the AI a hand-written map of internal adapters.
- [ ] Record:
  - number of KNEEKURA commands the AI had to discover manually before the first correct edit;
  - approximate context bytes/tokens loaded before the first correct edit, using the harness's available measurement rather than invented precision;
  - every invalid/unsafe operation the AI attempted or proposed;
  - TaskContext and evidence references used for the successful path;
  - whether a second fresh AI can resume from the retained handoff/context without repeating initial investigation.
- [ ] Save the minimized result to:
  - `departments/minecraft/mod-ai/verification/AI-USABILITY-ACCEPTANCE.json`
  - `departments/minecraft/mod-ai/AI-USABILITY-ACCEPTANCE.md`
- [ ] Preserve failures/friction in Failure / Repair History if they reveal a real system defect.
- [ ] Do **not** compute a universal usability score.

### MCP decision gate

After that trial:

- If CLI/JSON is adequate for the actual local AI harness, record `MCP: NOT_NEEDED` and stop.
- If the trial shows concrete transport friction that CLI/JSON cannot reasonably solve, create a **separate** bounded MCP spec/plan. It must call the same Python functions, have no state store/business logic, and pass CLI/MCP parity tests.
- Do not implement MCP merely because it was listed as a possible transport in the design.

---

## Plan Self-Review Result

- Spec coverage: TaskRequest, TaskContext target/evidence/capabilities/next-actions/lineage, CLI shape, compactness, error codes, security boundaries and real AI trial all have an owning task/gate.
- Type consistency: Tasks 2–5 consume the exact Task 1/3 interfaces defined above; CLI uses the same `prepare_task_context` path for both task subcommands.
- Review Focus: hostile text, stale identity, UNKNOWN retry, secret leakage and oversized context each have named regression coverage.
- Proportion: no new workflow engine or MCP implementation is planned; existing low-level adapters remain the implementation.
- Deliberate exclusion: asset part editing / before-after view tooling / retained UV-display editing remain in the separate deferred asset plan and are not required by this facade.

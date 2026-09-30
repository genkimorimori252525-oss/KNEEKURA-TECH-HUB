# Minecraft MOD-AI usability layer — design

Status: **FUTURE / DEFERRED UNTIL CURRENT UNIFIED PLAN IS CLOSED**  
Date: 2026-10-01  
Repository: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`  
Current implementation line: Draft PR #74  
Parent roadmap: `docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md`

**Implementation plan:** `docs/superpowers/plans/2026-10-01-minecraft-mod-ai-usability-layer.md`  
Implementation remains gated by Section 2; this link does not authorize starting early.

## 1. Purpose

KNEEKURA Minecraft MOD-AI already has many specialized capabilities: exact environment
capture, Source/Bytecode/resource search, mappings, Failure / Repair History, Core staging,
guarded Blockbench assets, Forge build/run contracts, GameTest, observer state, screenshots,
and bounded native input.

The next problem is no longer primarily capability scarcity. It is **AI operating cost**:
a coding agent must know which of many low-level surfaces applies now, which evidence is
current, what prerequisite is missing, and which action is safe to take next.

This follow-on work makes the existing system easier for an AI to operate without creating
a second MOD-AI brain or orchestration platform.

The desired user experience is:

```text
user: "Add homing danmaku to Reimu"
                ↓
AI asks KNEEKURA for one compact task context
                ↓
exact target + available evidence + capability readiness + blockers
                ↓
small set of valid next actions
                ↓
AI expands only the evidence it actually needs
                ↓
existing low-level KNEEKURA operations perform the work
```

The human should not need to understand the internal adapter topology for normal tasks.

## 2. Completion gate

This design is **not part of the current PR #74 acceptance work**.

Implementation may start only after one of these is true:

1. the current unified MOD-AI plan is completed for the user-approved scope; or
2. the user explicitly closes/defer-resolves any remaining current-plan acceptance gates
   and authorizes this follow-on stage.

An incomplete current acceptance item must not be renamed as a usability feature.

## 3. Audit findings

A light audit of the current branch found the following.

### Existing pieces to reuse

- `python -m kneekura_tech_hub.minecraft ...` already exposes stable JSON-oriented
  low-level operations.
- `capabilities` already exists.
- `context` already means research/Core context retrieval.
- Store/CAS, ProjectProfile, index snapshots, registries, contracts, sessions and receipts
  already provide authoritative identity.
- Current handoff/acceptance documents already explain product state to humans.
- Python functions underneath the CLI are reusable by another transport.
- `DEFERRED-IMPROVEMENTS-2026-09-30.md` already identifies current-state/next-action
  and artifact-lineage clarity as optional presentation improvements.

### Gaps relevant to AI usability

The existing `capabilities` output is mainly a **static command-surface inventory**.
It deliberately says command availability is not proof of installed tools or successful
integration. That is correct, but it means an agent still has to reconstruct readiness.

There is currently no compact task-scoped response that answers, in one bounded object:

- what exact Minecraft/loader/Java/profile/index this task is bound to;
- which evidence is already available;
- which capabilities are READY, NOT_CONFIGURED, BLOCKED, UNSUPPORTED or UNKNOWN;
- why a capability is not ready;
- which small set of operations is valid next;
- which artifact/receipt IDs should be retained for later expansion.

The CLI also exposes many low-level nouns. That is appropriate for the implementation,
but a host AI should not need to memorize the whole command graph for every task.

There is no repository MCP server today. Adding one before a stable AI-facing contract
would duplicate design work.

### Existing deferred work that stays separate

The asset-focused candidates in `DEFERRED-IMPROVEMENTS-2026-09-30.md` remain separate:

- stable part-addressed edits;
- comparable before/after views;
- bounded retained-asset texture/UV/display adjustments.

They are only implemented if a real editing task proves they are useful.

This usability layer absorbs only the overlapping **state/next-action** and
**artifact-lineage/delivery** concerns.

## 4. Design principles

### 4.1 Thin derived facade, not a new authority

The new layer derives answers from existing profiles, indexes, registries, sessions,
receipts and Store objects.

It must not introduce:

- another database;
- another scheduler;
- a persistent autonomous task state machine;
- another canonical knowledge plane;
- automatic Claim promotion;
- a second runtime authority;
- hidden launch/input permissions.

If the same authoritative inputs are supplied twice, the derived task context should be
deterministic apart from explicitly non-semantic request IDs/timestamps.

### 4.2 Read-only by default

Task preparation and capability discovery:

- do not run Gradle;
- do not launch Minecraft;
- do not contact Blockbench;
- do not execute providers;
- do not mutate worlds;
- do not send native input;
- do not consume launch budgets;
- do not perform network acquisition;
- do not write canonical Core records.

They may read explicitly supplied local KNEEKURA artifacts/registries and existing Store data.

### 4.3 Free text is data, never authority

A task may contain a natural-language goal, but that text cannot grant:

- paths;
- executables;
- provider selection;
- plugin installation;
- scripts;
- launch authority;
- native input authority;
- canonical promotion.

Routing uses explicit typed task intent plus validated KNEEKURA identities.

### 4.4 UNKNOWN never becomes "try again"

If a prior write/input/run is UNKNOWN, the usability layer may report reconciliation as
the next requirement. It must not recommend replaying the uncertain mutation.

### 4.5 Compact first, expand on demand

The default AI response should be small enough to stay in the coding model's active context.

Return:

- exact identities/hashes;
- short status summaries;
- blocker codes;
- evidence pointers;
- operation IDs.

Do not inline large source files, bytecode, logs or screenshots. Existing `search`,
`inspect`, `artifact read`, observation and capture surfaces remain the expansion path.

No embedding/vector database is required for this layer.

## 5. AI-facing contract

### 5.1 TaskRequest

Introduce one strict versioned request object for deriving an AI task context.

Conceptual shape:

```json
{
  "schema_version": 1,
  "intent": "edit_code",
  "goal": "Add homing danmaku to Reimu",
  "constraints": [],
  "acceptance": []
}
```

The initial `intent` vocabulary should remain small:

- `investigate`
- `edit_code`
- `create_asset`
- `verify_server`
- `verify_client`
- `compatibility_research`

`goal`, `constraints` and `acceptance` are inert descriptive data. The caller supplies
authoritative profile/index/registry/session references separately through the existing
trust boundaries.

Do not invent an all-purpose workflow language.

### 5.2 TaskContext

A derived TaskContext should expose five sections.

#### target

Exact known target identity:

- profile ID/hash if available;
- index snapshot ID if available;
- Minecraft version;
- loader/version;
- Java major;
- ANCHOR/FRONTIER/COMPARATIVE track;
- source/workspace revision where captured.

Unknown fields remain explicitly unknown.

#### evidence

Only compact pointers and counts relevant to the task:

- source/bytecode/resource availability;
- mapping availability;
- Failure / Repair History availability;
- selected acceptance/receipt IDs supplied by the caller;
- asset generation/export IDs when applicable;
- runtime/session evidence when applicable.

The facade does not manufacture stronger provenance.

#### capabilities

Each capability has two separate dimensions:

```text
surface: IMPLEMENTED | UNSUPPORTED
readiness: READY | NOT_CONFIGURED | BLOCKED | UNKNOWN
```

Examples:

- source_search
- bytecode_inspect
- mappings
- failure_history
- core_context
- blockbench_asset
- forge_build
- gametest
- server_observation
- client_observation
- native_input

A capability record includes:

- reason code;
- missing prerequisites;
- evidence/receipt reference when readiness depends on retained evidence.

Do not call something READY merely because its CLI command exists.

### 5.3 next_actions

Return a **small set of valid next operations**, not an autonomous plan.

Each entry contains:

- stable `operation_id`;
- why it is valid now;
- required explicit inputs still needed;
- whether it is read-only or side-effecting;
- whether separate human/user authorization is required.

Do not return arbitrary shell strings from untrusted text.

For deterministic cases, one entry may be marked `primary: true`.
If multiple next actions are equally valid, preserve the alternatives instead of forcing
a ranking.

Examples:

```text
profile.resolve
research.search
research.inspect
history.query
asset.prepare
build.registered
gametest.prepare
runtime.observe
runtime.reconcile_unknown
```

The facade itself does not execute these operations.

### 5.4 lineage

For outputs that a user/AI may need to hand off, expose one compact lineage summary:

```text
task request
 → profile/index
 → source generation
 → asset generation/export (if any)
 → build receipt/artifact
 → run/session receipt
 → observation/evidence
```

Use existing IDs/hashes. Do not create duplicate artifact identities.

## 6. CLI shape

Do not overload the existing `context` command; it already has research/Core semantics.

Add a narrow `task` namespace, conceptually:

```text
kneekura-minecraft ... task prepare
kneekura-minecraft ... task capabilities
```

`task prepare` returns the TaskContext.

`task capabilities` is a context-aware view over the same capability evaluator.

The existing top-level `capabilities` remains useful as static adapter discovery and may
be extended to clearly label itself as `STATIC_SURFACE`. It should not silently change
meaning into task readiness.

Avoid a `task run` command in the first implementation. Existing registered execution,
asset, input and observer routes already own mutations.

## 7. Simple happy path

The "happy path" is documentation plus TaskContext routing, not a hidden orchestrator.

For a typical code-editing task:

```text
task prepare
  ↓
profile.resolve if exact environment is missing
  ↓
task prepare again
  ↓
research.search / inspect / history.query
  ↓
host AI edits the workspace
  ↓
existing registered build
  ↓
existing contract + GameTest/observer path
  ↓
TaskContext/lineage summarizes what is now proven
```

For an asset task, the route uses the existing AssetRequest/guard/session/export path.
For compatibility research, it remains read-oriented unless a separate authorized runtime
experiment is explicitly chosen.

The host AI remains responsible for reasoning and deciding when evidence is sufficient.

## 8. Token/context-efficiency requirements

Default TaskContext must be bounded.

Initial design target:

- no large source/log/image bodies;
- no more than 12 capability entries in the compact view;
- no more than 5 next actions;
- blocker/reason strings short and machine-stable;
- IDs/hashes retained verbatim;
- human-readable explanation limited to concise summaries.

If the AI needs detail, it expands one referenced object with existing commands.

Do not add semantic embeddings merely to reduce context. Measure an actual task first.

## 9. Optional transport facade

Only after the CLI/TaskContext contract is stable, an MCP facade may be added.

MCP is **transport only**:

```text
AI client
   ↓
MCP stdio tool
   ↓
same Python task/capability/search/inspect functions
   ↓
existing KNEEKURA trust boundaries
```

Rules:

- no separate MCP business logic;
- no separate state store;
- no HTTP server merely for convenience;
- no broader permissions than the CLI;
- mutating tools require the same explicit registry/session/contract inputs;
- read-only tools remain read-only;
- CLI and MCP responses must pass parity/contract tests.

If the actual local AI harness works cleanly through CLI/JSON, MCP may remain unimplemented.
The success criterion is AI usability, not checking an MCP checkbox.

## 10. Error model

The facade should prefer typed blocker/reason codes over prose parsing.

Examples:

- `PROFILE_MISSING`
- `INDEX_STALE`
- `MAPPING_NOT_CONFIGURED`
- `PROVIDER_NOT_REGISTERED`
- `LAUNCH_NOT_AUTHORIZED`
- `SESSION_UNKNOWN_COMPLETION`
- `WINDOWS_INPUT_UNSUPPORTED`
- `EVIDENCE_SCOPE_INSUFFICIENT`

Prose may explain the code, but AI routing must not depend on matching English/Japanese text.

Stale or mismatched profile/index/session/artifact identities fail closed.

## 11. Security / governance invariants

The layer must preserve all current boundaries:

- registries remain the execution authority;
- task text cannot grant permissions;
- secrets/session authentication are never emitted in TaskContext;
- private machine paths are omitted or represented only when the existing public contract
  already exposes them safely;
- launch budgets are never created/increased;
- UNKNOWN writes/inputs are never replayed automatically;
- production worlds remain out of scope;
- human canonical gates remain unchanged;
- ANCHOR/FRONTIER/COMPARATIVE identities remain separate;
- guide/Reddit/video reconnaissance remains hypothesis/navigation, not implementation truth.

## 12. Acceptance criteria

A future implementation is accepted only when all of the following hold.

### Contract / determinism

- same authoritative inputs produce semantically identical compact TaskContext;
- stale/mismatched identities fail closed;
- unknown fields do not silently become known.

### No side effects

Tests prove `task prepare` / context-aware capability discovery cannot:

- spawn a process;
- contact a network service;
- start Blockbench/Minecraft;
- consume a launch/input budget;
- mutate Store except for an explicitly designed optional cache, which should be avoided;
- write Core/canonical records.

### Routing quality

Use at least these real-shaped fixtures:

1. no profile/index → next action requires environment capture;
2. exact indexed Forge target → source research is READY;
3. asset request with missing provider registry → asset mutation is NOT_CONFIGURED;
4. build receipt + prepared world → GameTest preparation is valid;
5. UNKNOWN input/run receipt → reconciliation is primary and replay is absent;
6. Linux client session → Linux input may be READY;
7. Windows target without backend → native input is UNSUPPORTED, not READY.

### Context bounds

Large indexes/histories do not cause proportional TaskContext growth.
Only counts/pointers appear until explicitly expanded.

### CLI / optional MCP parity

If MCP is implemented, the same inputs yield the same normalized contract as CLI calls,
excluding transport/request metadata.

### Real AI usability trial

After the original MOD-AI plan is closed, run one real coding-agent task through the facade.

Measure:

- how many KNEEKURA commands the AI had to discover manually;
- how much context was loaded before the first correct edit;
- whether it selected an unsafe/invalid operation;
- whether the retained evidence lets a second AI resume without re-investigation.

Do not create a universal numeric "AI usability score". Record the observed workflow and
specific friction.

## 13. Non-goals

This follow-on does not build:

- another autonomous coding agent;
- an AI planner service;
- a scheduler;
- a workflow engine;
- a new database;
- a vector DB/RAG platform;
- automatic issue/guide crawling;
- automatic canonical promotion;
- an automatic winner/recommendation engine for technical truth;
- a replacement for existing CLI/adapters;
- general Blockbench editing;
- Windows input unless separately selected as current acceptance work;
- speculative support for every Minecraft/loader version.

## 14. Relationship to other deferred improvements

`departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md` remains valid.

This design takes ownership of its secondary:

- current state / next action;
- artifact lineage / delivery clarity.

Its asset-editing Candidates 1–3 remain separate and need their own demonstrated task before
implementation.

If a future real MOD task reveals that recreate-from-spec is insufficient, select the relevant
asset-editing candidate then; do not implement it merely because this usability layer exists.

## 15. Stop condition

This stage is complete when a coding AI can receive one compact authoritative TaskContext,
identify the few valid next operations without reading the internal adapter map, expand only
the evidence it needs, and continue through the existing safe KNEEKURA operations without a
second state system.

Stop there.

Future convenience features require a demonstrated task failure or friction record, consistent
with the TECH HUB core preservation rule.

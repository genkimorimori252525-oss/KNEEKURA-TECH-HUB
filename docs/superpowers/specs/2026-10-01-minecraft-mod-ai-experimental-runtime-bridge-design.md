# KNEEKURA TECH HUB × LAB Experimental Runtime Bridge v1

Status: **FUTURE / POST-COMPLETION DESIGN — DO NOT IMPLEMENT INSIDE THE CURRENT MOD-AI PLAN**  
Date: 2026-10-01  
TECH HUB repository: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`  
LAB repository: `genkimorimori252525-oss/KNEEKURA-LAB`  
TECH HUB branch reviewed for this design: `jolly/minecraft-mod-ai-assets-2026-09-28`  
TECH HUB reviewed head: `072dd1e56a0a5c64b2d6175813f418ffa453722f`  
LAB main reviewed during design: `21959d439960d112d05c4c3ee44e54e353246d4e`

Parent roadmap:
- current MOD-AI: `docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md`
- post-completion AI usability layer:
  `docs/superpowers/plans/2026-10-01-minecraft-mod-ai-usability-layer.md`

> This document defines the **next architectural stage after those plans**.
> It does not expand PR #74 acceptance, authorize a Minecraft launch, merge KNEEKURA-LAB
> into this repository, or grant any new runtime/mutation permission.

---

## 1. Goal

Turn KNEEKURA-LAB into the **experimental runtime instrument** for KNEEKURA TECH HUB.

TECH HUB should investigate, design, implement and build a MOD. LAB should receive a
bounded experiment, run it in real Minecraft, collect structured + visual + timeline
evidence, and return an evidence-linked result that TECH HUB's AI can use to diagnose,
repair and re-verify the MOD.

The target loop is:

```text
user goal
   ↓
TECH HUB TaskContext
   ↓
gameplay reconnaissance + source + bytecode + mappings + history
   ↓
hypothesis / implementation
   ↓
code + Blockbench assets
   ↓
exact Forge build
   ↓
ExperimentRequest
   ↓
KNEEKURA-LAB
   ↓
resettable Arena
   ↓
typed actions
   ↓
Probe + cameras + event timeline
   ↓
ExperimentResult
   ↓
TECH HUB AI
   ↓
repair / next experiment
   ↓
before-after verification
   ↓
Failure / Repair History
```

The long-term product is not "Minecraft recreated in a browser." Real Minecraft remains
the authority for runtime, rendering, entity behavior, networking and interaction.

---

## 2. Completion / start gates

Do not implement this bridge until all of the following are true, or the user explicitly
changes the order.

### TECH HUB prerequisites

1. The current unified MOD-AI plan has been closed for the user-approved scope.
2. The AI usability layer has a stable TaskContext / capability-readiness contract, or the
   user explicitly chooses to integrate the bridge before that layer is implemented.
3. Existing provenance, run-contract, Observer, GameTest and Failure / Repair History
   boundaries remain intact.

### LAB prerequisites

Re-audit KNEEKURA-LAB at implementation time. The reviewed design already has the right
direction, but this document does not assume all future LAB gates are complete.

At minimum, the bridge must have real equivalents of:

- debug/run identity and runtime attestation;
- resettable bounded Arena;
- typed world/entity/scenario actions;
- Evidence Broker or equivalent compact query surface;
- immutable RunSnapshot;
- raw evidence retention;
- clean shutdown / evidence finalization.

G3 Arena/actions and G4 deep/ring-buffer observation concepts in the current LAB roadmap are
especially relevant.

If a prerequisite is missing, implement the smallest prerequisite in the repository that
owns it; do not duplicate it in the other repository.

---

## 3. Repository boundary

Keep the repositories separate.

### TECH HUB owns

- user/task intent;
- exact target ProjectProfile/index;
- source/bytecode/mapping/history research;
- code and asset creation;
- exact Forge build identity;
- experiment design and fixed assertions;
- interpretation of ExperimentResult;
- repair decisions;
- retained Failure / Repair History;
- AI-facing TaskContext.

### KNEEKURA-LAB owns

- disposable Minecraft debug runtime;
- debug session / RunSnapshot identity;
- Arena lifecycle and reset;
- typed runtime actions;
- Probe observation;
- camera capture;
- ring buffer / trigger capture;
- runtime evidence retention;
- compact experiment evidence production;
- bounded cleanup.

### The bridge owns only

- `ExperimentRequest` validation;
- mapping TECH HUB identities into LAB's experiment identity;
- explicit handoff to an authorized LAB execution path;
- `ExperimentResult` validation/import;
- evidence lineage between the two systems.

The bridge must not become a third runtime authority, database, scheduler or agent.

---

## 4. Primary contracts

### 4.1 ExperimentRequest

TECH HUB sends one strict, versioned experiment description.

Conceptual shape:

```json
{
  "schema_version": 1,
  "experiment_id": "homing-004",
  "target": {
    "profile_id": "sha256...",
    "index_snapshot_id": "sha256...",
    "build_artifact_hash": "sha256...",
    "source_revision": "..."
  },
  "arena": {
    "preset": "normal",
    "baseline_hash": "sha256..."
  },
  "subjects": [],
  "initial_state": [],
  "actions": [],
  "observation_scopes": [],
  "visual_rig": {
    "mode": "cardinal-4-snapshot-v1"
  },
  "assertions": [],
  "time_budget_ms": 30000
}
```

The final implementation may use different field names, but these semantics are mandatory.

#### Request invariants

- experiment identity is explicit;
- target build/profile/index/revision are explicit;
- Arena identity/baseline is explicit;
- actions are typed operations, not raw shell/Minecraft/WorldEdit command text;
- observation scopes are explicit and bounded;
- assertions are fixed before execution;
- time/action/capture budgets are explicit;
- visual capture is requested by capability, not by arbitrary camera script;
- free text cannot grant authority;
- no credentials/secrets are embedded.

Changing an assertion after seeing the result creates a new experiment generation.

### 4.2 ExperimentResult

LAB returns a strict result linked to the original request and RunSnapshot.

Conceptual shape:

```text
experiment_id
request_hash
run_snapshot_id

execution
  status
  action_receipts
  cleanup

observations
  structured_summary
  timeline_summary
  visual_bundle

assertions
  per_assertion results

gaps
  missing / stale / unavailable evidence

evidence
  immutable hashes / locators
```

Execution completion and MOD behavior are separate.

A successfully executed experiment may still produce FAIL / UNKNOWN / NOT_RUN assertions.

---

## 5. Assertion-first experiment design

Every experiment should declare what would count as success/failure before runtime mutation.

Example for a homing projectile:

```text
projectile is spawned
target UUID is acquired
distance-to-target decreases for the declared window
projectile does not clip through the declared obstacle
expected target receives declared damage
unrelated entity does not receive the effect
```

Assertions should prefer machine-observable facts where possible.

Do not use a visual impression when the Probe can return the exact fact.

Changing the acceptance test after observing the run is a new experiment revision, not a
reinterpretation of the old result.

---

## 6. RunSnapshot as the cross-repository evidence anchor

LAB's existing RunSnapshot concept becomes the runtime anchor for bridge evidence.

A bridge run should preserve, as applicable:

- TECH HUB experiment request hash;
- TECH HUB profile/index/build identities;
- source revision / dirty state;
- Minecraft version;
- Forge version;
- Java version;
- loaded MOD IDs/versions/hashes;
- config hash;
- resource/model hashes;
- Arena baseline hash;
- Probe version/hash;
- observation schema version;
- debug profile;
- debugSessionId / runId / epochs.

A later code/config/resource change never upgrades an old PASS to the new state.

Old evidence remains historical. Current verification becomes `REVERIFY_REQUIRED` when its
dependency fingerprint changes.

---

## 7. Observation model: three complementary evidence planes

AI debugging should combine three evidence planes.

### Structured State

Use Probe/runtime APIs for facts Minecraft already knows precisely:

- entity UUID/type;
- position/rotation/velocity;
- bounding box;
- health/effects;
- owner/target;
- navigation/path/collision;
- projectile identity/lifecycle;
- blocks/fluids/collision shapes;
- selected inventory/equipment;
- packet milestones;
- Molang/animation/render milestones where instrumented.

### Visual Evidence

Use screenshots for facts that really require seeing:

- model clipping / sinking / floating;
- broken textures or UVs;
- wrong silhouette;
- animation presentation;
- particles;
- visual readability;
- camera-dependent rendering defects.

### Timeline Evidence

Use ordered events for causal context:

- actions;
- target changes;
- goal start/stop;
- navigation recompute;
- projectile spawn/hit/remove;
- damage;
- packets;
- Molang milestones;
- render milestones;
- exceptions;
- capture triggers.

One evidence plane must not impersonate another.

---

## 8. AI-specific rule: never ask Vision to rediscover structured facts

This is a non-negotiable principle.

If Minecraft/Probe already knows an exact fact, expose that fact directly instead of asking
a vision model to infer it from pixels.

Examples:

```text
position       -> Probe
target UUID    -> Probe
health         -> Probe
cooldown       -> Probe
collision      -> Probe
packet         -> Probe
navigation     -> Probe

model clipping -> visual review
texture break  -> visual review
silhouette     -> visual review
particle look  -> visual review
legibility     -> visual review
```

Visual evidence supplements structured evidence; it does not replace precise telemetry.

---

## 9. Cardinal-4 Multi-View Camera Rig

### 9.1 v1: Snapshot Rig

The default AI visual rig is four canonical Arena viewpoints:

```text
                 NORTH
                   ↓

        WEST → [ ARENA ] ← EAST

                   ↑
                 SOUTH
```

Do **not** launch four permanent Minecraft clients.

v1 uses one authoritative client/runtime and captures four virtual viewpoints around a
controlled observation state.

The first implementation should use a safe observation barrier/frozen scenario state where
possible:

```text
reach capture barrier
    ↓
record exact state identity
    ↓
north
east
south
west
    ↓
release barrier
```

Each frame records at least:

- experiment/request identity;
- RunSnapshot;
- subject UUID(s);
- server/client tick/frame interval available to that capture;
- camera transform;
- FOV;
- viewport;
- image hash;
- raw/derived status.

The four frames may be near-sequential render frames, but they must refer to the same
controlled experiment state. Do not call them "same-frame" unless they truly are.

### 9.2 v2: Synchronized Multi-Pass — deferred

Only implement same-render-frame multi-target rendering if a real defect proves Snapshot Rig
insufficient.

Possible future direction:

```text
one Minecraft client frame
  -> North RenderTarget
  -> East RenderTarget
  -> South RenderTarget
  -> West RenderTarget
```

This is deeper renderer intervention and therefore intentionally deferred.

Examples of demonstrated need:

- one-frame pose corruption;
- transient particle/render artifact;
- state changes too quickly for the Snapshot Rig barrier.

If no such need appears, v2 remains unimplemented.

---

## 10. Visual Evidence Compiler

Raw camera frames are immutable evidence.

For one capture set retain:

- `north`
- `east`
- `south`
- `west`

Then produce derived AI-friendly views.

### Contact sheet

Default first visual for the AI:

```text
+-------------+-------------+
| NORTH       | EAST        |
|             |             |
+-------------+-------------+
| SOUTH       | WEST        |
|             |             |
+-------------+-------------+
```

The contact sheet is derived and points back to the four raw images.

AI should inspect the compact sheet first and open an individual source image only when
needed.

### Annotation layer

Annotations are derived from structured Probe data, never guessed from the image when exact
telemetry exists.

Examples:

- target bounding box;
- subject label / UUID suffix;
- velocity vector;
- navigation target/path;
- collision marker;
- projectile trajectory;
- Arena bounds.

Keep:

```text
RAW_FRAME
DERIVED_ANNOTATED_FRAME
```

as separate artifacts.

An annotation defect never changes the underlying image.

---

## 11. Visual Evidence Bundle

One AI-facing visual capture unit should bind images to structured state and timeline context.

Conceptual bundle:

```json
{
  "experiment_id": "homing-004",
  "capture_id": "capture-12",
  "state_window": {
    "server_tick_start": 1842,
    "server_tick_end": 1842
  },
  "subjects": ["uuid..."],
  "cameras": {
    "north": "sha256:...",
    "east": "sha256:...",
    "south": "sha256:...",
    "west": "sha256:..."
  },
  "contact_sheet": "sha256:...",
  "annotated_contact_sheet": "sha256:...",
  "structured_summary": "sha256:...",
  "timeline_window": "sha256:..."
}
```

The exact schema will be fixed during implementation, but it must preserve independent raw
and derived identities.

---

## 12. Event-triggered visual capture

Do not record four full-resolution views every tick.

Reuse LAB's ring-buffer / trigger philosophy.

Candidate triggers:

- target change;
- damage;
- projectile spawn/hit/remove;
- navigation stuck;
- entity exits Arena;
- invariant failure;
- M5 without M6;
- render-lane anomaly;
- exception/crash;
- AI explicit capture.

A trigger may retain a bounded sequence such as:

```text
pre-roll
trigger
post-roll
```

For selected cases this may become:

```text
T-20
T-10
T
T+10
T+20
```

The exact sampling window is experiment/config-specific. It must be bounded and recorded.

This is preferred over feeding long raw gameplay videos to the AI.

---

## 13. Before / After verification

A repair experiment should support matched comparison.

```text
Build A
  -> same ExperimentRequest semantics
  -> Evidence A

Build B
  -> same Arena baseline + assertions + camera rig
  -> Evidence B
```

Generate derived comparison artifacts:

```text
North A | North B
East A  | East B
South A | South B
West A  | West B
```

Also compare structured/timeline facts.

Before/After comparison must reject or clearly mark non-comparable runs when key conditions
differ, including:

- Arena baseline;
- experiment/assertion generation;
- camera/FOV/viewport;
- subject setup;
- target MOD/config/resource identity.

A pixel difference is not automatically an improvement.

---

## 14. Evidence Bundle returned to TECH HUB

TECH HUB should receive a compact summary first.

Example:

```json
{
  "experiment_id": "homing-004",
  "outcome": "PARTIAL",
  "subject": "uuid...",
  "state": {
    "position": [12.2, 64.0, 8.5],
    "velocity": [0.03, 0.0, -0.18],
    "navigation": "ACTIVE",
    "collision": false
  },
  "events": [
    "TARGET_CHANGED",
    "PROJECTILE_SPAWN"
  ],
  "assertions": [],
  "visual_bundle_hash": "sha256:...",
  "timeline_hash": "sha256:..."
}
```

Large traces and images are drill-down artifacts.

This follows the same AI rule as TaskContext:

> **Compact first. Expand on demand.**

---

## 15. Observation, Finding, Hypothesis and Conclusion remain separate

Adopt LAB's existing TECH HUB-derived epistemic separation.

```text
Runtime Evidence
    ↓
Observation
    ↓
Finding
    ↓
Hypothesis
    ↓
Conclusion
```

LAB/Probe writes runtime facts.

AI-written interpretations reference Observation/Evidence IDs.

An AI hypothesis must never be re-presented later as OBSERVED truth simply because it was
saved previously.

Cause candidates may remain multiple/ambiguous.

No confidence/popularity heuristic automatically chooses a winner.

---

## 16. TECH HUB TaskContext integration

After the AI usability layer is accepted, extend its capabilities with an experimental runtime
surface rather than bypassing it.

Conceptually:

```text
experimental_runtime:
  surface: IMPLEMENTED
  readiness: READY | NOT_CONFIGURED | BLOCKED | UNKNOWN
```

Possible next operations:

- `experiment.prepare`
- `experiment.inspect_result`
- `experiment.compare`
- `experiment.reconcile_unknown`

TaskContext never executes an experiment.

The host AI selects an operation, then the existing explicit authority mechanism authorizes the
LAB action.

No automatic unbounded experiment loop is introduced by TaskContext.

---

## 17. Transport / execution boundary

v1 architecture defines the logical bridge first.

Implementation must prefer a **local explicit registered adapter** over a new network service.

Requirements:

- exact LAB checkout/tool identity;
- explicit executable/entrypoint registration;
- bounded request/result files or stdio;
- no arbitrary executable supplied by ExperimentRequest;
- no hidden long-lived daemon requirement;
- no internet-facing bridge;
- no credentials in evidence;
- same request ID / experiment ID cannot silently execute twice;
- uncertain mutation remains UNKNOWN;
- cleanup is bounded and recorded.

The implementation plan must re-audit LAB's then-current machine entrypoints before choosing
the concrete local transport. Do not copy a historical CLI path merely because this document
names the repository.

---

## 18. Integration with Blockbench asset work

Blockbench and LAB solve different visual problems.

### Blockbench loop

```text
Generate
 -> capture static model views
 -> AI visual review
 -> repair
 -> export
```

This is already proven for the Celestial Staff slice.

### LAB loop

```text
Forge-integrated asset/code
 -> real Minecraft scenario
 -> Probe state + multi-view capture
 -> AI runtime/visual review
 -> repair
```

Do not replace Blockbench editor review with the LAB, and do not claim Blockbench visual review
proves in-game visual correctness.

The two loops become consecutive layers.

---

## 19. Phased implementation roadmap

### X0 — Freeze bridge contracts

Define and test:

- ExperimentRequest;
- ExperimentResult;
- bridge identity/linkage;
- error/UNKNOWN semantics.

No Minecraft launch.

### X1 — Bind TECH HUB identity to LAB RunSnapshot

Prove exact build/profile/index/request identities survive the handoff and appear in returned
evidence.

No new evidence DB.

### X2 — Arena + typed action integration

Use LAB's resettable Arena and typed controls.

Prove:

- baseline identity;
- bounded mutation;
- reset fidelity;
- action receipts;
- partial apply / interruption handling.

### X3 — Cardinal-4 Snapshot Camera Rig

Implement one-client four-view capture with exact camera/capture identity.

Start with explicit capture only.

### X4 — Visual Evidence Compiler

Add:

- 2×2 contact sheet;
- structured-data-derived annotation;
- compact visual bundle;
- raw/derived lineage.

### X5 — Trigger / ring-buffer integration

Bind selected anomaly/event triggers to bounded pre/post capture.

Do not enable continuous full-resolution recording.

### X6 — Before / After comparison

Prove matched experiment/camera/baseline requirements and generate derived comparison bundles.

### X7 — TaskContext integration + one real MOD repair cycle

Run one real task:

```text
investigate
 -> edit
 -> build
 -> experiment
 -> observe
 -> repair
 -> same experiment
 -> compare
 -> verify
 -> record lesson
```

A second AI should be able to resume from the retained evidence without replaying the initial
investigation.

### X8 — Same-frame multi-pass camera only if earned

Implement synchronized multi-pass only after a concrete defect demonstrates that X3 cannot
capture the required phenomenon.

If no such defect occurs, mark X8 `NOT_NEEDED`.

---

## 20. Acceptance requirements

The bridge is not complete because four screenshots were produced.

Acceptance requires at least:

### Identity

- ExperimentResult matches the exact ExperimentRequest;
- TECH HUB build/profile/index identities match the LAB RunSnapshot;
- stale code/config/resource evidence is rejected/reverification-required.

### Arena

- reset returns to the declared baseline within the supported scope;
- mutations outside allowed bounds are rejected;
- interrupted/partial mutation cannot become PASS.

### Structured evidence

- selected subjects are bound by exact UUID/experiment identity;
- UNKNOWN / NOT_TRACKED / NOT_RENDERED / NOT_LOADED remain distinct;
- raw evidence and AI interpretations stay separate.

### Camera

- four canonical viewpoints point to the same controlled experiment state;
- camera/FOV/viewport and temporal intervals are retained;
- raw images are independently addressable;
- contact/annotated sheets derive from them;
- no "same-frame" claim is made for sequential Snapshot Rig captures.

### AI efficiency

- default result is compact;
- raw logs/images/traces are fetched only when needed;
- structured facts are not reconstructed by Vision;
- one real debugging task demonstrates reduced manual navigation versus using raw low-level
  surfaces alone.

### Repair verification

- one real defect is reproduced;
- an implementation repair is made;
- the same experiment/assertions are re-run;
- before/after comparison is valid;
- no unrelated regression is silently hidden;
- the new failure/repair lesson is retainable in existing TECH HUB history.

---

## 21. Security and authority invariants

- experiment text cannot grant execution permission;
- raw Minecraft commands are not the normal AI-facing bridge contract;
- no production world;
- no caller-supplied executable path;
- no arbitrary Blockbench/Minecraft script;
- no automatic retry after uncertain mutation;
- no automatic launch-budget increase;
- no automatic canonical Claim promotion;
- no replacement of LAB/TECH HUB identity checks;
- no interpretation of image existence as visual PASS;
- no interpretation of action completion as gameplay PASS;
- no interpretation of render capture as synchronization/performance PASS;
- no four-client permanent camera farm by default;
- no internet-exposed debug service merely for convenience.

---

## 22. Non-goals

This design does not require:

- moving KNEEKURA-LAB source into TECH HUB;
- deleting LAB's existing Viewer/render research;
- recreating Minecraft rendering in WebGL as runtime authority;
- continuous multi-angle video ingestion;
- computer vision reconstruction of world state;
- a new Evidence database;
- a universal AI/debug quality score;
- a new autonomous Planner/Agent service;
- infinite self-running experiments;
- same-frame four-view rendering before a demonstrated need;
- support for every loader/version.

---

## 23. Relationship to LAB's existing design

The reviewed LAB direction already contains many required ideas:

- real-Minecraft-first authority;
- dedicated debug runtime;
- debugSession/run/experiment/action/observation identity;
- persistent/resettable Arena;
- typed Control API;
- L0–L4 observation;
- ring buffer / pre-trigger capture;
- Evidence Broker;
- Observation != Conclusion;
- immutable RunSnapshot;
- stale verification;
- cause candidates;
- deep render/network/YSM probes;
- G1–G7 debug-workspace progression.

Therefore the future integration should **reuse those concepts, not rebuild them in TECH HUB**.

At implementation time, re-audit current LAB code and keep only responsibilities that survived
its own evolution.

---

## 24. Stop condition

The stage is complete when TECH HUB can hand one bounded, identity-bound experiment to LAB and
receive enough structured + timeline + multi-view visual evidence for an AI to diagnose and
verify one real MOD repair, with before/after proof and preserved uncertainty.

Stop there.

Additional camera sophistication, richer automatic anomaly detection, larger scenario libraries
or more autonomous loops require demonstrated debugging friction.

The guiding principle is:

> **Use Minecraft as the truth-bearing experiment, Probe as precise instrumentation, cameras
> for genuinely visual facts, and the AI for hypothesis and iteration.**

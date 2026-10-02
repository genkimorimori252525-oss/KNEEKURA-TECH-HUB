# KNEEKURA TECH HUB × LAB Experimental Runtime Bridge v1

Status: **APPROVED POST-COMPLETION DESIGN — SOURCE IMPLEMENTATION AUTHORIZED 2026-10-01; LIVE ACCEPTANCE DEFERRED**
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

> This document defines the **next architectural stage after those plans**. The user subsequently authorized implementation on 2026-10-01 and prioritized source implementation while deferring real-device validation. The original plan boundaries below remain the design basis; current source interfaces and explicit acceptance gaps are recorded in `departments/minecraft/mod-ai/LAB-SCOPED-CONTROL.md`.
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

### 1A. 2026-10-01 dual-presentation audit conclusion

A light follow-up audit compared this bridge design with the current KNEEKURA-LAB main
(`21959d439960d112d05c4c3ee44e54e353246d4e`) and TECH HUB bridge state
(`56aab10509d8b55f560d50ac8984814eedf5ae80` before this update).

The existing LAB design already establishes several boundaries that support a combined
human/AI environment:

- real Minecraft remains the authoritative visual/test environment;
- the Human Workbench is presentation/control, not a second Minecraft renderer;
- camera automation is already recognized as a possible experiment perturbation;
- strict render preconditions separate TRACKED / IN_RENDER_RANGE / RENDER_ENTERED / YSM states;
- Evidence Cut / snapshot-barrier concepts already exist for coherent observations;
- raw Evidence and AI Finding/Hypothesis/Conclusion are separate;
- the old live Web Viewer is not required as the primary real-Minecraft runtime view.

The audit therefore rejects two tempting designs:

1. **Two independent truth modes** — "Human Mode" and "AI Mode" with different runtime state.
   This risks debugging one state while presenting another.
2. **One compromised presentation for both audiences.** A screen optimized for dense AI
   diagnostics is unnecessarily hostile to a human, while a beautiful human screen omits
   machine-readable evidence the AI needs.

The selected rule is **Dual Presentation, Single Truth**: one runtime/evidence truth,
separate derived presentations for a human and for the AI.

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

The AI is never treated as an unquestionable visual oracle. Visual conclusions are scoped
to explicit checks and evidence, and the packet format itself must be benchmarked against
known Minecraft debugging cases before it becomes the default.

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

## 11A. AI Visual Observation Packet

The AI-facing visual unit is not "four screenshots." It is a deliberately structured
observation packet that removes avoidable spatial ambiguity before asking a vision model
to reason about appearance.

The default packet should contain, in this order:

1. experiment / RunSnapshot / capture identity;
2. compact structured facts;
3. exact top-down spatial schematic;
4. Cardinal-4 RGB contact sheet;
5. explicit visual questions;
6. drill-down references to original views and optional debug views;
7. bounded event timeline;
8. matched before/after comparison when a repair is being verified.

### Exact top-down schematic

Generate a machine-derived top-down map from Probe/world facts, not from vision inference.

It should be able to show, when available:

- Arena bounds;
- selected entity positions;
- exact entity IDs;
- bounding-box footprints;
- facing/velocity vectors;
- navigation target/path;
- projectile positions/trajectory;
- collision/contact markers;
- named observation points.

The schematic is a derived artifact with its own hash and source Observation IDs.
It must never replace raw world/Probe evidence.

Its main purpose is to solve cross-view correspondence for the AI: the model should not
have to infer whether an entity in NORTH and EAST is the same entity when KNEEKURA already
knows the exact UUID.

### Stable subject labels across views

Each selected subject receives one stable short label for the capture set, for example:

```text
A = Reimu / UUID …91af
B = Zombie / UUID …720c
C = projectile / entity …13
```

The same label is used on every derived view and the top-down schematic.

Color may be used as an additional cue, but color alone is not identity. Text label +
underlying exact UUID/entity identity is authoritative.

### Hierarchical visual drill-down

Do not give every full-resolution image to the AI by default.

Use:

```text
Level 0: structured summary + top-down schematic + 2×2 RGB contact sheet
Level 1: one or two selected original camera views
Level 2: bounded crop around the relevant subject/region
Level 3: optional diagnostic render such as ID/depth/collision/path view
```

The host AI requests deeper levels only when the previous level leaves a concrete visual
question unresolved.

This is the visual equivalent of TaskContext's "compact first, expand on demand" rule.

### Explicit visual-check contract

Do not use an unconstrained prompt such as "look for anything wrong" as the primary
acceptance oracle.

An experiment may attach bounded visual checks such as:

```text
VIS-01 subject A feet below declared ground plane?
VIS-02 subject A mesh clips the declared obstacle?
VIS-03 expected texture region missing/corrupted?
VIS-04 projectile visually appears on the wrong side of the obstacle?
```

Allowed visual answers should be explicit:

- `YES`
- `NO`
- `NOT_VISIBLE`
- `AMBIGUOUS`

Each answer references the camera/debug-view evidence used.

A visual check may support a visual finding. It does not overwrite a contradictory
structured fact, and `NOT_VISIBLE` / `AMBIGUOUS` must remain unresolved.

---

## 11B. Optional diagnostic visual channels

RGB is the default human/AI appearance view, but the system may derive narrowly scoped
diagnostic images when a visual question needs them.

Useful candidate channels:

### Entity-ID mask

Render selected entities/projectiles with flat stable IDs/colors and background separation.

Purpose: object correspondence and occlusion, not visual quality.

### Depth view

A normalized depth representation for the declared camera.

Purpose: clarify front/behind relationships when RGB is ambiguous.

### Collision / bounds view

Show authoritative collision shapes, entity bounding boxes and Arena/world contacts.

Purpose: diagnose clipping/penetration without asking vision to infer geometry from textures.

### Navigation/path view

Project the structured path/target/velocity information into camera/top-down coordinates.

Purpose: combine visual presentation with exact navigation evidence.

These are **derived debugging artifacts**, not new runtime truth. Every channel must retain
the source Observation IDs and camera transform used to derive it.

Do not implement all channels in X3/X4 by default. Start with top-down schematic + entity
labels; add a diagnostic channel only when a real visual-debugging case benefits from it.

---

## 11C. Dual Presentation, Single Truth

Human and AI consumers may receive different presentations, but they must reference the same
runtime truth.

```text
                  authoritative experiment truth
            RunSnapshot + Experiment + Evidence Cut
                            |
                +-----------+-----------+
                |                       |
        Human Presentation        AI Presentation
                |                       |
        natural / interactive      explicit / diagnostic
        readable / attractive      compact / machine-readable
```

There is no requirement that the human and AI look at the same layout, camera or overlay.
There **is** a requirement that every presentation be bound to the same declared run,
experiment generation, subject identities and evidence window.

### Human presentation surfaces

The default human experience should remain a normal, understandable Minecraft laboratory.

Three presentation levels are allowed:

1. **Human Normal View**
   - ordinary Minecraft scene;
   - natural/free/subject-follow camera chosen for human usability;
   - minimal experiment status;
   - no requirement to display AI-only diagnostic channels.

2. **Human Debug View**
   - opt-in overlays such as subject identity, target, path, collision, health, current
     experiment, timeline marker and AI-flagged evidence;
   - overlays are derived presentation, not raw evidence;
   - turning an overlay on/off does not rewrite observations or assertions.

3. **Human Evidence Review**
   - inspect a retained capture, event, before/after pair or AI Finding;
   - jump from an AI flag to the exact tick/window/view/evidence IDs that support it;
   - review historical evidence without pretending it is current runtime state.

The Human Workbench must not reimplement Minecraft/YSM rendering as a second authority.

### AI presentation surface

The AI receives the Visual Observation Packet defined above:

- compact structured summary;
- exact top-down schematic;
- canonical Cardinal-4 contact sheet;
- stable subject labels;
- explicit visual checks;
- selected timeline;
- drill-down links;
- optional ID/depth/collision/navigation diagnostic views.

The AI presentation may be generated without being shown in the human UI.

### Shared truth binding

Every presentation record that participates in debugging must retain enough identity to prove
what it represents:

- `runSnapshotId`;
- `experimentId` and experiment generation/request hash;
- relevant `evidenceCut`;
- Arena/arenaEpoch;
- selected subject UUIDs;
- camera/capture identity where visual;
- raw source artifact hashes;
- derived-presentation identity.

If one of these identities changes during capture/review, do not silently combine the old and
new presentation.

### Raw scene versus presentation overlays

KNEEKURA diagnostic overlays must not contaminate the raw visual evidence they explain.

Prefer this derivation:

```text
Minecraft scene/render result
        |
        +--> RAW_SCENE_RGB
        |       |
        |       +--> AI crop/contact sheet
        |       +--> AI annotation
        |
        +--> HUMAN_PRESENTED_FRAME (optional)
                + Minecraft/HUD as intended
                + KNEEKURA human overlays
```

`RAW_SCENE_RGB` is captured before KNEEKURA-specific human/AI annotation when technically
possible.

A screenshot of the exact human composite may also be retained when the bug concerns UI/HUD or
when proving what the human actually saw, but it is a different artifact and must not replace
the clean scene capture.

### Human camera and AI camera coexistence

The preferred implementation is a non-perturbing AI capture camera/render target that does not
take control of the human's active gameplay camera.

If the first real implementation cannot provide that safely, a bounded fallback may temporarily
take camera control only under an explicit visual-capture barrier:

1. record exact pre-capture human camera/presentation state;
2. establish the experiment/evidence capture barrier;
3. capture canonical AI views;
4. restore the exact prior human camera state;
5. record the capture as a perturbation.

A capture that moves the actual client camera or changes tracking/render eligibility cannot be
silently reused as evidence for a behavior assertion that the camera perturbation could affect.

In such cases, separate the behavior experiment from the visual-observation experiment or mark
the relevant assertion `INCONCLUSIVE`.

### Presentation-only versus experiment-affecting interaction

Human controls are classified before implementation.

**Presentation-only examples:**
- panel layout;
- selecting a retained evidence item;
- overlay visibility;
- contact-sheet zoom;
- timeline browsing of already captured evidence.

These must not mutate Minecraft experiment state.

**Observation-affecting examples:**
- free camera movement that changes tracking/render range;
- changing FOV when FOV matters to the visual check;
- forcing a render view;
- opening a Minecraft screen that pauses an integrated runtime.

Record these as observation perturbations.

**Experiment mutations:**
- pause/slow-motion mechanisms;
- teleporting subject/player;
- changing blocks/entities;
- changing time/weather/config;
- issuing scenario actions.

These go through the typed Control/Experiment action path and receive normal action receipts.
They are never hidden as UI behavior.

### AI-to-human evidence feedback

The AI may surface findings back into the Human Workbench.

A finding card should identify, as applicable:

- finding/hypothesis ID;
- experiment;
- subject;
- tick/frame/time window;
- camera/view;
- visual-check result;
- evidence IDs;
- epistemic status;
- short explanation.

Example:

```text
AI visual flag
Experiment: homing-004
Subject: A / Reimu
View: EAST
Window: tick 1842
Check: VIS-01
Result: YES
Finding: possible right-foot ground penetration
[open evidence]
```

Displaying a finding never promotes it to OBSERVED truth or changes experiment acceptance.

### Quality priority

When a trade-off genuinely cannot be avoided, use this order:

1. **Evidence correctness and reproducibility**
2. **AI diagnosability**
3. **Human debugging usability**
4. **Human visual polish**

This does not mean human UX is unimportant. The architecture intentionally separates
presentation so that Human usability can usually improve without weakening AI evidence.

### Observation-cost / observer-effect budget

Human and AI presentation must not silently make the target behavior less trustworthy.

Measure and retain, where relevant:

- screenshot/camera capture duration;
- render-frame cost;
- Probe queue/drop changes;
- client/server tick impact;
- capture frequency;
- whether a capture barrier/pause/camera takeover occurred.

Continuous high-cost AI diagnostic rendering is not the default. Human display may remain live,
while expensive AI evidence channels are generated on explicit or event-triggered demand.

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

### X4 — Visual Evidence Compiler + dual presentation

Add:

- 2×2 contact sheet;
- stable cross-view subject labels;
- exact top-down schematic derived from Probe/world facts;
- structured-data-derived annotation;
- explicit bounded visual-check records;
- hierarchical original/crop/debug-view drill-down;
- compact visual bundle;
- raw/derived lineage;
- Human Normal / Human Debug / Human Evidence Review presentation boundary;
- AI presentation generation independent of whether it is shown to the human;
- raw-scene versus human-composite artifact separation;
- presentation/observation/mutation interaction classification.

Prefer non-perturbing AI camera capture. If the real platform requires temporary camera takeover,
implement the recorded capture-barrier fallback and prove exact restoration before using it.

Run the initial KNEEKURA-specific visual-format benchmark before freezing the default AI packet.
Start with RGB + labels + top-down schematic; diagnostic ID/depth/collision/path channels are
added only when the benchmark or a real debugging task demonstrates value.

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

### Dual human / AI presentation

- Human and AI presentations resolve to the same RunSnapshot / experiment / evidence window;
- human overlays cannot alter raw evidence;
- raw scene and optional human-composite captures remain distinct;
- presentation-only UI operations do not mutate experiment state;
- camera/FOV/render changes that can affect observation are recorded as perturbations;
- any experiment mutation initiated from the Human Workbench goes through the typed action path;
- AI findings shown to the human remain Findings/Hypotheses with evidence references, not promoted Observations;
- an AI evidence capture does not require the human to look at or manually provide screenshots.

### AI efficiency

- default result is compact;
- raw logs/images/traces are fetched only when needed;
- structured facts are not reconstructed by Vision;
- stable subject labels and the exact top-down schematic remove avoidable cross-view ambiguity;
- the AI can answer bounded visual checks with YES / NO / NOT_VISIBLE / AMBIGUOUS and evidence references;
- drill-down reaches original/cropped/diagnostic views without loading every image by default;
- one real debugging task demonstrates reduced manual navigation versus using raw low-level
  surfaces alone.

### Vision-format benchmark

Before treating the visual packet format as stable, build a small KNEEKURA-specific benchmark
whose expected visual conditions are known independently of the vision model.

Representative cases should include:

- normal/no-defect control;
- entity partially below ground;
- mesh/block clipping;
- visible texture omission/corruption;
- wrong-facing or obviously displaced body part;
- projectile on the wrong side of an obstacle;
- partial/full occlusion;
- a case where RGB is ambiguous but structured/depth/ID evidence disambiguates it.

Compare at least these information formats on the **same cases**:

```text
A. one RGB view
B. four raw RGB views
C. Cardinal-4 contact sheet
D. contact sheet + stable entity labels + exact top-down schematic
E. D + structured state/timeline summary
F. E + one task-relevant diagnostic view when requested
```

Record per-check outcomes and failure modes. Do not collapse them into a universal "vision
score" or assume the most information-dense format is always best.

The selected default packet should be the simplest format that materially improves the real
debugging checks while keeping context cost bounded.

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

The same accepted experiment must also be reviewable through a human-oriented presentation
without changing the underlying evidence, and the AI must be able to generate its diagnostic
packet without requiring the human to capture or curate screenshots manually.

Stop there.

Additional camera sophistication, richer automatic anomaly detection, larger scenario libraries
or more autonomous loops require demonstrated debugging friction.

The guiding principle is:

> **Use Minecraft as the truth-bearing experiment, Probe as precise instrumentation, cameras
> for genuinely visual facts, and the AI for hypothesis and iteration.**

# LAB On-Demand Motion Trace Design / Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Preserve KNEEKURA's evidence boundary: raw observations are evidence; motion lines, summaries and overlays are derived presentation.

**Goal:** Add an on-demand spatial motion-trace system to Water Tank Studio so a human or implementation AI can inspect how a selected Mob or ranged attack actually moved without keeping trajectory graphics permanently visible. Recording remains bounded and available for later inspection; rendering/compilation happens only when explicitly requested.

**Architecture:** Reuse existing LAB observations and SimLab position history as the source of truth. Do not create a second motion database and do not make a new renderer authoritative. A small trace extractor converts retained position samples into a versioned derived `SampledMotionTrace`; Human Viewer and AI Visual Observation Packet consume the same trace contract. Default Viewer state is trace OFF. Raw Minecraft imagery remains clean; trajectory overlays are separate derived artifacts bound to exact run/entity/time/source identities.

**Authoritative baseline:** `KNEEKURA-TECH-HUB/main` after the 2026-10-02 canonical-baseline declaration. Existing approved runtime-bridge design already calls for exact top-down schematics, velocity/navigation overlays and projectile trajectory. This plan fills the missing general-entity, time-windowed trajectory layer without replacing that design.

## 1. Product decision

The feature is named **On-Demand Sampled Motion Trace**.

It is deliberately broader than the old projectile-only Viewer `trail`, but narrower than a generic always-on telemetry renderer.

The default behavior is:

1. record the already-authorized bounded motion observations;
2. draw no trajectory line;
3. when a human or AI selects a subject and asks for movement history, derive a trace from retained observations;
4. render only the requested subject/window;
5. discard the derived in-memory drawing when closed while retaining the underlying evidence according to the existing evidence lifecycle.

This means **recording and rendering are independent**.

A trace being invisible does not mean it was not recorded. Turning a trace on does not change Minecraft state, camera state, AI state or the evidence source.

## 2. Non-goals

- No permanent spaghetti-lines over every entity.
- No all-world entity scan.
- No second evidence store or trajectory database.
- No continuous screenshot/video recording.
- No claim that a line between two sampled points is the exact continuous path.
- No guessed AI intent.
- No guessed projectile trajectory for attacks that do not expose a projectile/beam/ray source.
- No modification of raw Minecraft screenshots to make an overlay look authoritative.
- No requirement to build a new 3D WebGL trajectory engine before the existing plan/elevation views prove insufficient.

## 3. Truth model

### 3.1 Raw evidence

Raw position/velocity/identity observations remain authoritative for what was sampled.

Typical sources are:

- SimLab `pos` lane for existing arena traces;
- Debug Workspace `SERVER_ENTITY_STATE` for exact selected/registered subjects;
- existing projectile spawn/position/gone/hit observations where available;
- typed action receipts and timeline rows for explicit teleport/reset/control events;
- `NAVIGATION` / `BRAIN_MEMORY` only for declared navigation state.

### 3.2 Derived trace

A `SampledMotionTrace` is presentation derived from those observations.

Each visible point must retain:

- run / RunSnapshot identity;
- Arena identity/epoch when applicable;
- entity UUID or stable trace entity ID;
- entity type and trace class;
- tick / gameTime / retained timestamp available at source;
- exact sampled XYZ;
- velocity if directly observed;
- source Observation ID / source trace row identity;
- source kind.

Each segment must identify its two endpoint samples and carry:

- `semantics: SAMPLED_ENDPOINT_CONNECTION`;
- elapsed ticks/time;
- `continuity: DISPLAY_DERIVED` unless a stronger source explicitly proves continuous geometry.

The UI and AI packet must never describe this as an exact continuous path.

### 3.3 Gaps and discontinuities

Never bridge evidence gaps invisibly.

Break the drawn line when:

- the entity is gone/missing across the requested interval;
- source continuity is not retained;
- dimension/world identity changes;
- Arena/run identity changes;
- the sample gap exceeds the source-specific allowed continuity window;
- a reset boundary invalidates continuity.

Explicit typed teleports may be shown as a distinct discontinuity marker because the control receipt is direct evidence. Unknown jumps must not be relabelled as teleports by inference.

## 4. Trace classes and visual grammar

Color is never the only discriminator. Use **color + line pattern + width + point marker** so the result remains readable under color-vision differences and monochrome review.

### 4.1 MOB_ACTUAL

For Mob/entity body movement.

- visually heavier than projectile trace;
- dashed or long-dash center line;
- circular measured-sample nodes;
- current entity position emphasized;
- optional latest directly observed velocity vector;
- top-down X/Z trace plus vertical representation.

Purpose: wandering, pursuit, strafing, hovering, orbiting, retreating, flying and path-following behavior.

### 4.2 PROJECTILE_ACTUAL

For an actual projectile entity or instrumented ranged-attack object.

- visually thinner and brighter than Mob trace;
- different dash cadence or solid/short-dash grammar;
- small diamond/sample markers;
- spawn and terminal event markers when directly known;
- hit/gone/collision event may be attached only from retained event evidence.

Purpose: arrows, fireballs, spell projectiles and comparable entity-backed attacks.

### 4.3 NAVIGATION_DECLARED

For a path/target directly exposed by Minecraft/TLM navigation evidence.

- visually separate from actual movement;
- fine dotted guide style;
- labelled **planned/declared navigation**, never actual trajectory;
- hidden automatically when no authoritative navigation/path evidence exists.

A Ghast or custom flying AI that does not expose a navigation path must show `NOT_AVAILABLE`, not a fabricated planned line.

### 4.4 Optional future ranged classes

Hitscan, beam or ray attacks may later add a separate `RANGED_RAY_OBSERVED` class only if the MOD/runtime exposes exact endpoints or geometry. Do not infer it from particles or animation.

## 5. Human Viewer behavior

### 5.1 Default state

**Motion Trace OFF.**

No trace canvas/WebGL work should run simply because motion data exists.

### 5.2 Selection

A human selects an entity/projectile and opens **軌跡 / Motion Trace**.

Controls:

- trace class toggles: Mob / Projectile / Navigation;
- time window presets: short / medium / long;
- bounded custom window where supported;
- view: top-down, elevation, existing 3D/F3 context;
- measured-point visibility;
- event marker visibility.

The initial implementation should reuse the current Viewer time controls and existing `trail` concept rather than build a second playback clock.

### 5.3 Multi-trace comparison

Permit a small bounded number of explicitly selected traces to be shown together.

Typical comparison:

- Mob actual motion;
- its projectile actual trajectory;
- declared navigation path.

Do not automatically enable every nearby entity.

### 5.4 Spatial views

Phase 1 should prioritize:

1. **Plan / XZ:** route shape, circling, approach, avoidance and horizontal drift;
2. **Elevation:** altitude change and vertical oscillation;
3. existing scene context when useful.

For flying mobs, the plan trace alone is insufficient. The vertical view is required for a complete debugging read.

A later 3D tube/ribbon renderer is deferred unless real debugging cases show plan + elevation are insufficient.

## 6. AI-facing interface

AI use is first-class, but the AI should not receive a giant trajectory dump by default.

### 6.1 Progressive disclosure

Level 0 Visual Observation Packet remains compact.

A packet may state that retained motion history is available:

```text
motion_trace_available:
  subject A: MOB_ACTUAL
  projectile C: PROJECTILE_ACTUAL
  navigation A: AVAILABLE
```

The AI explicitly requests a trace only when movement is relevant to diagnosis.

### 6.2 Trace request

Conceptual request:

```json
{
  "subject": "exact-uuid-or-trace-id",
  "classes": ["MOB_ACTUAL"],
  "window": {"endTick": 12345, "durationTicks": 120},
  "views": ["PLAN_XZ", "ELEVATION"],
  "includeMetrics": true
}
```

The final API shape must use existing LAB identity/request conventions rather than introducing a free-form executable channel.

### 6.3 AI response

Return structured facts before graphics.

Recommended derived summary:

- trace class;
- sample count;
- exact first/last sample tick;
- retained duration;
- net displacement;
- sampled polyline length;
- min/max altitude;
- directly observed speed statistics where valid;
- number/location of gaps;
- event markers;
- source identity list;
- epistemic label: `DERIVED_FROM_SAMPLED_OBSERVATIONS`.

Then provide SVG/other bounded visual artifacts:

- plan trace;
- elevation trace;
- optional overlay attached to an existing diagnostic view.

This lets the AI reason numerically first and inspect geometry only when helpful.

## 7. Recording policy

### 7.1 Reuse first

Do **not** add a new high-rate motion recorder until real fixtures demonstrate that existing retained sampling is insufficient.

The first implementation derives Mob traces from the current exact-subject/server-state and SimLab position histories.

### 7.2 Scope

"Always recorded" means **always within the already declared experiment/registered-subject scope**, not every entity in the whole world.

The system must remain bounded by:

- registered/selected subjects;
- already tracked projectiles/events;
- existing Arena/run identity;
- existing evidence retention/budgets.

### 7.3 Sampling quality metadata

Every trace carries its actual sampling cadence/gaps.

A five-tick subject sample is shown as five-tick sampled evidence; the line must not pretend to be one-tick truth.

If a real test (fast projectile, high-speed flying boss, tight orbit) proves the cadence inadequate, add a later **bounded high-resolution motion lane** with an explicit experiment budget. That is a separate measured optimization decision, not part of the first implementation by default.

## 8. Existing Viewer migration

The current SimLab Viewer already has:

- time playback/scrubbing;
- `trail` window control;
- projectile-only trail drawing;
- plan + elevation views;
- `trackOf(id)` over the position lane.

Refactor rather than duplicate.

### Required migration

- extract projectile-only trail building into a generic trace builder;
- remove presentation logic that equates `role === projectile` with "the only entity allowed to have history";
- keep projectile styling as one trace class;
- allow explicit selected Mob/entity history;
- preserve old projectile behavior and fixtures;
- do not turn all Mob traces on by default.

The legacy projectile `trail` control becomes the first UI consumer of the common motion-trace layer.

## 9. Visual Evidence Compiler integration

The current top-down compiler shows current bounds/facing and one-tick velocity. Extend it only on request.

Add a derived artifact such as:

```text
DERIVED_SAMPLED_MOTION_TRACE_V1
```

with:

- structured trace JSON;
- plan SVG;
- elevation SVG;
- source Observation IDs;
- raw source hashes/identities where existing evidence contracts require them;
- requested subject/window/classes;
- explicit sampled/derived semantics.

The normal Cardinal-4 raw frames remain untouched.

The existing top-down snapshot can optionally reference the trace artifact; it should not silently grow a historical path into every packet.

## 10. Events and debugging annotations

When evidence exists, traces may attach markers for:

- projectile spawn;
- hit/collision/gone;
- behavior transition;
- target change;
- navigation path change;
- explicit typed teleport;
- reset/epoch boundary;
- AI phase/mode change.

Markers must reference the underlying timeline/Observation ID.

No marker may be created merely because the path "looks like" an event occurred.

## 11. Performance and storage rules

- Trace rendering default OFF.
- No periodic draw loop dedicated to hidden traces.
- No new duplicate full position history if existing stores already retain the samples.
- Derived trace is computed lazily and may be cached only by exact immutable identity + window + trace version.
- Cache invalidates on run/epoch/source identity mismatch.
- Bound selected trace count and requested sample count.
- Long histories may be visually decimated **only as a presentation layer**; the artifact must preserve the relationship to the original samples and must say that visual decimation occurred.
- Never decimate the underlying evidence.

## 12. Accessibility / readability

Distinct trace classes must remain distinguishable without color.

Use at least three independent cues:

- line pattern;
- line width;
- point marker shape.

Labels should identify exact subject aliases/UUID suffixes consistently with the Visual Observation Packet.

Dense paths should support focus mode: selecting one trace dims other derived traces without changing raw evidence.

## 13. Implementation tasks

### Task 1 — Contract and fixtures

- [ ] Define `SampledMotionTrace v1` schema and epistemic labels.
- [ ] Define gap/discontinuity rules and source-specific continuity metadata.
- [ ] Add fixtures for ground Mob, Ghast-like 3D wandering, projectile arc, Mob + projectile pair, missing samples, gone entity, explicit teleport, run/epoch boundary.
- [ ] Assert segments always reference retained sample endpoints and never claim exact continuous motion.

### Task 2 — Generic trace extractor

- [ ] Build a source-neutral extractor over retained position observations.
- [ ] Reuse SimLab `trackOf`/position store where applicable.
- [ ] Add Debug Workspace adapter for exact retained subject observations without creating a second database.
- [ ] Produce structured metrics and gap list.
- [ ] Keep extraction read-only.

### Task 3 — Viewer migration

- [ ] Refactor old projectile-only trail code into common trace rendering.
- [ ] Add explicit selected-entity Mob trace.
- [ ] Keep trace OFF by default.
- [ ] Add distinct Mob/Projectile/Navigation visual grammar.
- [ ] Support plan + elevation and current playback/scrub controls.
- [ ] Ensure turning traces off produces no trace draw work.

### Task 4 — Projectile linkage

- [ ] Preserve projectile spawn/position/gone/hit identity where already observed.
- [ ] Permit explicit owner/target linkage only when retained evidence provides it.
- [ ] Do not infer projectile paths for uninstrumented ranged attacks.
- [ ] Verify Mob and projectile traces can be overlaid without identity ambiguity.

### Task 5 — AI Visual Packet integration

- [ ] Add `motion_trace_available` capability summary.
- [ ] Add bounded explicit trace request.
- [ ] Generate structured trace + plan/elevation derived artifacts lazily.
- [ ] Bind artifact to exact run/Arena/entity/time/source evidence.
- [ ] Keep raw Cardinal-4 frames unmodified.
- [ ] Add drill-down references from visual checks/findings to the requested trace.

### Task 6 — Navigation comparison

- [ ] Map directly observed `NAVIGATION` / PATH evidence into `NAVIGATION_DECLARED`.
- [ ] Keep it visually/semantically distinct from `MOB_ACTUAL`.
- [ ] Return `NOT_AVAILABLE` for entities such as flying/custom AI when no path is exposed.
- [ ] Never derive "intended path" from actual movement.

### Task 7 — Performance and regression

- [ ] Measure Viewer idle/off state and prove no hidden trace rendering loop.
- [ ] Measure requested trace generation on short/medium/long windows.
- [ ] Bound sample/trace count and cache identity.
- [ ] Run existing Viewer/projectile tests to preserve prior trail behavior.
- [ ] Run Visual Evidence Compiler/packet tests and LAB CI.
- [ ] Use real or faithful Ghast-like/high-speed fixture to decide whether existing sampling cadence is adequate before proposing a high-resolution lane.

## 14. Acceptance criteria

The feature is complete only when all of these are true:

1. A selected Mob can display a historical motion trace on demand.
2. A selected projectile can display its trajectory using a visibly different grammar.
3. Mob and projectile traces can be shown together without relying on color alone.
4. Default Viewer state draws neither trace.
5. Underlying bounded observations remain available while visualization is off.
6. Every displayed measured point maps back to retained source identity.
7. Missing evidence creates a visible break; no silent gap interpolation.
8. Plan + elevation make a flying-Mob trace understandable without requiring a new 3D renderer.
9. AI can request one exact subject/window and receive compact structured metrics plus derived visual artifacts.
10. Raw Minecraft screenshots are unchanged by trajectory overlays.
11. Navigation/intent is shown only from explicit navigation evidence and is labelled separately.
12. Existing projectile trail behavior/regressions remain green.
13. No second evidence database, world scan or always-on trajectory renderer is introduced.

## 15. First real validation scenarios

### A. Ghast-like wander

Validate that a flying subject's horizontal loops/drift and altitude oscillation are readable in plan + elevation. Confirm five-tick or existing source cadence honestly appears as sampled points.

### B. Ghast fireball

Show Mob actual trace and fireball actual trajectory simultaneously. The two must remain visually distinct and independently selectable.

### C. Pursuit/navigation Mob

Overlay actual Mob motion and directly observed navigation path. Verify they cannot be mistaken for each other.

### D. Missing/gapped evidence

Drop/omit a bounded sample interval in a fixture and prove the renderer breaks the line rather than hiding the gap.

### E. Explicit teleport

Use a typed teleport receipt and show a discontinuity marker instead of a normal movement segment.

## 16. Deferred decisions

Do not decide these until evidence shows need:

- one-tick always-on motion sampling for every registered subject;
- full 3D trajectory ribbons/tubes;
- curvature/orbit classifiers;
- automatic anomaly classification from path shape;
- long-term cross-run trajectory warehouse;
- ray/beam visualization without direct runtime geometry.

These are possible future layers, not prerequisites for the useful first version.

## Design summary

The core rule is:

```text
bounded observations are retained
        ↓
nothing is drawn by default
        ↓
human/AI asks about one exact subject/window
        ↓
SampledMotionTrace is derived read-only
        ↓
structured facts + plan/elevation visualization
        ↓
close the view; raw evidence remains
```

This preserves Water Tank Studio's strongest property: it can collect precise runtime facts without forcing the human or AI to stare at all of them at once.

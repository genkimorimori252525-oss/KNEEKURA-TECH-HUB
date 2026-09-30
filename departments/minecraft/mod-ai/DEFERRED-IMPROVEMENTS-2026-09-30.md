# Deferred MOD-AI usability improvements

> **AI-operability follow-on:** the broader post-completion TaskContext / capability-discovery / thin-facade design is recorded in
> [2026-10-01-minecraft-mod-ai-usability-layer-design.md](../../../docs/superpowers/specs/2026-10-01-minecraft-mod-ai-usability-layer-design.md).
> That design owns the secondary "current state / next action" and artifact-lineage concerns below; asset-editing Candidates 1–3 remain separate.

Status: **DEFERRED — DO NOT IMPLEMENT BEFORE CURRENT-PLAN COMPLETION.**

Requested on 2026-09-30. This records possible follow-on work; it does not
authorize starting it, close an acceptance gap, or enlarge the current plan.
The [current handoff](HANDOFF-2026-09-30.md) and
[unified implementation plan](../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md)
remain the execution priority. An unresolved requirement stays unresolved;
renaming it a future improvement does not satisfy this gate.

## Purpose and existing scope

Make a demonstrated asset-repair task easier for the existing coding AI and
the person reviewing it. Keep only improvements whose value survives a real
task; discard unnecessary wishlist items.

The first static Java-item slice is deliberate. The current system already
creates bounded geometry and palette texture regions, captures model/native
JSON and PNGs, applies fixed display transforms, retains evidence in Store,
exports validated resources, and observes the game. Those are working
capabilities, not missing foundation work. Screenshot capture already exists.

The current guard only exposes begin, texture, texture_region, cube, inspect,
and capture. Texture regions are prepared before geometry; display transforms
are fixed by the guard. A general repair of an existing part is not currently
an exposed operation. The following proposals address that narrower limitation.

| Category | Examples | Treatment |
|---|---|---|
| Intentional first-slice boundary | One static Java item; no GeckoLib or animation; fixed display policy | Preserve unless a later concrete task requires another format |
| Existing planned acceptance | Remaining M4 views/synchronization, U/A fault cases, exact-version research limits | Finish through the current plan; do not count as new usability features |
| Optional asset-repair improvement | Change one retained part; compare the same view before/after; adjust bounded UV/texture/display fields | Consider only after the completion gate and a demonstrated need |
| Optional presentation improvement | Make current evidence status and next action easier to read; make artifact delivery easier to trace | Reuse existing receipts, IDs and output paths; avoid another state system |

## Completion gate

Before selecting any implementation below:

1. Reconcile every unchecked current-plan item against its original acceptance
   criterion and exact executed evidence. Keep Windows, dedicated-client,
   version/dependency and human-governance limitations explicit.
2. Complete the requested current-plan scope or obtain an explicit user decision
   about an actual blocked acceptance requirement. A fixture PASS cannot stand
   in for an unrun live observation.
3. Confirm that the user still wants the candidate improvement and identify
   the concrete editing/review task it will improve.

Saving this document satisfies only the request to retain a deferred plan.
No automatic scheduler, launch, implementation or later activation follows.

## Candidate 1: stable part-addressed edits

Use a retained asset's request/project/generation identity plus a stable logical
part ID to change a narrowly allowlisted property of that part. Prefer extending
the existing guard/session over exposing upstream update commands wholesale.

Investigation and implementation order, if selected later:

1. Reproduce a useful repair on the retained static-item workflow. Record the
   exact part, property, intended change and fields that must remain unchanged.
2. Inspect the pinned provider's actual supported update API and native IDs.
   Define how a logical part maps to the owned native element; names alone
   must not silently select duplicate or recreated elements.
3. Add a minimal operation with expected generation/old-value checks, bounded
   values, a new resulting generation, and exact before/after capture hashes.
4. Reject missing/duplicate/recreated targets, stale snapshots, wrong projects,
   unexpected geometry changes, invalid UVs and unknown completion. Preserve
   quarantine and no-blind-retry behavior.
5. Verify one real repair in the owned disposable editor and revalidate export.

Do not add hierarchy/animation/general script editing merely to implement one
part change. If recreating the small asset already solves the real task well,
this candidate can be dropped.

## Candidate 2: comparable before/after views

Reuse the existing capture path. Store the view parameters and both artifact
generations so a reviewer can compare the same camera/projection/viewport.
Label a pair non-comparable when those conditions differ; do not invent an
automatic aesthetic score or treat a pixel difference as correctness.

If selected, first demonstrate where existing capture receipts are insufficient,
then add only the missing view metadata/comparison presentation. Test changed
camera/viewport, stale generations and missing captures. A host review remains
separate from structural checks and in-game acceptance.

## Candidate 3: bounded texture, UV and display adjustments

Extend only properties required by a real repair. Current texture regions and
fixed display transforms already exist; the candidate is controlled adjustment
of a retained asset, not a new texture or screenshot subsystem.

For a selected change, retain palette/texture-size/resource limits, exact owned
texture and face identity, finite UV/display ranges and no-overwrite export.
Require unchanged unrelated parts/faces/slots and re-run native/model/PNG
equivalence checks. In-game inventory/first-/third-person review remains its
own acceptance. Arbitrary brushes, file/URL imports, plugins and scripts stay
outside this proposal.

## Secondary candidates

### Current state and next action

If users cannot tell what is ready, blocked or next from the existing CLI and
receipts, present a compact derived summary: current generation, separate
structural/visual/runtime results, concrete blocker and one valid next action.
Do not introduce a second state machine, scheduler or autonomous agent service.
An UNKNOWN receipt must not become a retry suggestion.

### Artifact lineage and delivery

Reuse existing profile, request, generation, capture, export, build and receipt
hashes. If delivery is confusing, provide one small manifest/readme stating the
actual downloadable file, target versions, hash, source/build relation and
which artifact was really exercised. A source PR is not a downloadable JAR;
development-class runtime evidence is not an installed-distribution launch.
Do not expose raw private receipts, tokens, internal paths or environment IDs.

## Review and stop conditions

Each selected candidate must have one concrete task, a small reviewed design,
focused failure cases, compatible export/evidence behavior, and actual editor
acceptance where necessary. Reuse Store, observer, runner and history. Do not
create another database, knowledge graph, run manager or canonical truth plane.

Stop when the demonstrated repair/review task works. Drop features that do not
earn their cost. None of these candidates is implemented by this document.

# Deferred MOD-AI usability improvements

Status: **ASSET CANDIDATES 1–3 DEFERRED; SECONDARY FACADE IMPLEMENTED,
ACCEPTANCE PENDING.**

Requested on 2026-09-30. The
[original scoped plan](CURRENT-ACCEPTANCE-2026-09-30.md) is now complete for the
bounded Linux/X11 staff pilot and original research/regression criteria.
Historical pending gates in the [handoff](HANDOFF-2026-09-30.md) remain historical;
they must not be presented as the current acceptance state or rewritten as PASS.

The approved [AI Usability Layer design](../../../docs/superpowers/specs/2026-10-01-minecraft-mod-ai-usability-layer-design.md)
and [implementation/trial plan](../../../docs/superpowers/plans/2026-10-01-minecraft-mod-ai-usability-layer.md)
own the secondary state/next-action and artifact-lineage concerns below.
Their bounded implementation is documented in [TASK-CONTEXT.md](TASK-CONTEXT.md).
Focused task/CLI and installed-layout packaging regressions pass locally;
exact-head hosted CI and the actual AI trial still gate completion and secondary
presentation acceptance. MCP remains undecided pending the trial; neither MCP
nor the LAB runtime bridge is implemented here.

Asset-editing Candidates 1–3 remain **DEFERRED** and are not authorized or
implemented by that facade. Retaining a proposal does not activate it, launch
anything, change permissions or enlarge the accepted scope.

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
| Original scoped acceptance | M4 views/synchronization and original U/A result kinds | Closed in the current acceptance record; keep Windows/performance/U06 and other declared limits explicit |
| Optional asset-repair improvement | Change one retained part; compare the same view before/after; adjust bounded UV/texture/display fields | Consider only after the completion gate and a demonstrated need |
| Secondary presentation improvement | Make task-scoped evidence/readiness and next action easier to read; retain artifact lineage | Implemented as a thin read-only facade; hosted CI and real AI usability acceptance remain pending |

## Completion gate

Before selecting any asset Candidate 1–3 implementation below:

1. Reconcile every unchecked current-plan item against its original acceptance
   criterion and exact executed evidence. Keep Windows, dedicated-client,
   version/dependency and human-governance limitations explicit.
2. Complete the requested current-plan scope or obtain an explicit user decision
   about an actual blocked acceptance requirement. A fixture PASS cannot stand
   in for an unrun live observation.
3. Confirm that the user still wants the candidate improvement and identify
   the concrete editing/review task it will improve.

The original scoped completion prerequisite is now met; the candidate-selection
and demonstrated-need requirements remain. No automatic scheduler, launch,
asset implementation or later activation follows from this document.

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

## Secondary concerns owned by the AI Usability Layer

### Current state and next action

**Bounded code implementation present; presentation acceptance pending.**
`task prepare` derives exact target identity, compact evidence, separate
capability surface/readiness/reason codes, and at most five fixed next-action
recommendations. It uses existing registries, receipts and validators, with no
second state machine, scheduler or autonomous agent service. UNKNOWN completion
selects read-only reconciliation and suppresses new side-effecting advice;
it never becomes a retry suggestion. Structural, visual and runtime evidence
retain their original limited meanings.

The focused four-file task/CLI suite passed **996 tests** and installed-layout
packaging passed **5 tests** for this documentation checkpoint. These verify
code behavior and packaging, not demonstrated AI usability. Exact-head hosted CI
and the real task/fresh-agent-resume trial remain open before claiming this
secondary presentation concern accepted.

### Artifact lineage and delivery

**Bounded lineage implementation present; presentation acceptance pending.**
The same facade returns existing profile/index/session/evidence references and
hash-verified evidence pointers. It does not create a second artifact manifest,
new canonical IDs, a download service or a package delivery claim. Use existing
`search`, `inspect` and `artifact read` to expand the needed evidence, with actual
file delivery handled through the existing authorized workflow.

A source PR is not a downloadable JAR; development-class runtime evidence is
not an installed-distribution launch. The facade must not infer source/build
or exercised-artifact equivalence beyond the retained checks. Public summaries
exclude raw private receipts, tokens, private paths and endpoint selectors;
a hash does not authorize sharing the artifact's contents. The actual AI trial
still needs to establish whether this bounded lineage is useful for handoff and
resume, rather than declaring all possible delivery concerns solved.

## Review and stop conditions

Each selected candidate must have one concrete task, a small reviewed design,
focused failure cases, compatible export/evidence behavior, and actual editor
acceptance where necessary. Reuse Store, observer, runner and history. Do not
create another database, knowledge graph, run manager or canonical truth plane.

Stop when the demonstrated repair/review task works. Drop features that do not
earn their cost. Candidates 1–3 remain unimplemented; the separate bounded
secondary facade implementation above does not close its pending acceptance
gates or authorize further asset/runtime work.
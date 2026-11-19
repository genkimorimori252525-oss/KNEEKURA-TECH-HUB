# Visual evidence compiler and matched comparison: source handoff

This implements the source layer of approved bridge milestones X4 and X6. It does not attest that a MOD was launched, a capture succeeded in Minecraft, a repair passed, or the provisional AI format won a real-task benchmark. Those live gates remain deferred.

## Ownership and inputs

`compileVisualPacket` takes the existing initialized `EvidenceStore` and a canonical capture Observation ID. The canonical payload is the direct `cardinal4_capture_manifest` produced by X3. It reads the same store prefix and source images, preserving the evidence cut, RunSnapshot, experiment generation/request hash, Arena identity, exact subjects, and tick/frame windows. There is no new runtime owner or canonical database.

The capture must be COMPLETE and RESTORED. Restoration is supported by X3's exact `MINECRAFT_API_READBACK` expected/observed state, including observed unpause and screen restoration. This source check is not an owner/runtime attestation. Incomplete/uncertain captures remain available as canonical historical evidence but are refused by this complete-packet compiler.

The compiler consumes the camera worker's strict `visual-capture.mjs`. The exact matrix convention is `JOML_COLUMN_MAJOR_CAMERA_RELATIVE`: subtract camera position from a world point, multiply the retained same-frame renderer view matrix, then the projection matrix. Reconstructing this from yaw or quaternion would lose renderer transforms.

## Output and local review

The compiler emits actual hash-addressed artifacts:

- 2×2 PNG contact sheet: NORTH/EAST, SOUTH/WEST, with 18-pixel view headers
- A distinct PNG sheet with structured projected bounds and stable A–P labels
- Exact world X/Z SVG schematic with Arena bounds, subject footprints, facing, and one-tick velocity vectors
- Compact JSON structured facts, bounded attributed timeline, and an independently identified AI packet
- Optional bounded crops from original RGB views (at most 1,048,576 pixels)
- Optional static local HTML evidence review with Normal, Debug, and Evidence Review panels

The HTML uses local relative hash-addressed image links and CSS radio controls. It has no script, network request, runtime control, or second Minecraft/YSM renderer. Every panel is labeled retained evidence; the existing Minecraft runtime remains responsible for the live normal scene. The AI packet is produced independently of human visibility or panel mode. The optional human composite slot stays null; a future human screenshot must use its own artifact role and cannot replace RAW_SCENE_RGB.

Example inside the existing Node evidence host, after its store has been initialized:

```js
import { compileVisualPacket, persistVisualPacket } from './debug-workspace/evidence/visual-compiler.mjs';
import { createEvidenceReviewArtifact } from './debug-workspace/evidence/visual-presentation.mjs';

const compiled = await compileVisualPacket({
  store: runtime.store,
  sourceObservationId: captureObservationId,
  visualChecks: [{
    checkId: 'VIS-01', subjectUuid, question: 'Are the feet below the declared ground?',
    answer: 'NOT_RUN', evidenceViews: [],
  }],
  timelineObservationIds: selectedCanonicalObservationIds,
});
const review = createEvidenceReviewArtifact({ packet: compiled.packet });
compiled.artifacts.push(review);
await persistVisualPacket({ store: runtime.store, compiled });
// Open runDir + '/' + review.ref.path locally. This only browses retained evidence.
```

Persistence uses `evidence/derived/visual/<sha256>.<extension>` under the existing run. It refuses symlinks, changed bytes, foreign packet/artifact lineage, and finalized-run writes. Packet/artifact hashes and nested bindings are validated before human presentation. Raw files and canonical observations are never modified. Existing retained derived artifacts can be reviewed after finalization; this API deliberately does not reopen finalized runs for writes.

The manifest Observation ID and producer frame-row receipt hash are distinct fields. The latter is labeled `EXACT_PRODUCER_FRAME_ROW_BYTES`; it is not a hash of the canonical manifest or a JavaScript re-encoding of the producer row. The controlled-state hash likewise keeps producer-byte semantics rather than making a false cross-language canonicalization claim.

## Visual questions and attribution

Answers are bounded `YES`, `NO`, `NOT_VISIBLE`, `AMBIGUOUS`, or `NOT_RUN`, with exact source camera hashes. Uncertain answers remain unresolved. Questions/answers support inferred visual findings, never rewrite structured facts or turn pixel changes into acceptance. Experiment assertions remain fixed in the registered request; these presentation questions do not change them.

AI feedback cards must reference an existing packet check, its subject/result/view, and exact retained source image. Cards carry the original epistemic status and no acceptance effect. Timeline entries preserve scope, source, observation ID, and resource epoch; unselected entity context is explicitly marked. The selected timeline does not claim event continuity.

`classifyInteraction(type)` is a closed classification API. Panel selection, overlay visibility, sheet zoom, and retained timeline browsing are presentation-only. Free camera/FOV/render/screen changes route to observation control with a perturbation receipt. Pause, teleport, block/entity/time/config changes, and scenario actions route to typed Control with receipts. No non-presentation interaction executes from the HTML.

## Matched comparison

```js
import { compareVisualRuns } from './debug-workspace/evidence/visual-comparison.mjs';
import { persistDerivedArtifacts } from './debug-workspace/evidence/visual-artifacts.mjs';

const compared = await compareVisualRuns({
  before: { store: beforeStore, sourceObservationId: beforeCapture, requestBytes: beforeRequestBytes },
  after: { store: afterStore, sourceObservationId: afterCapture, requestBytes: afterRequestBytes },
  intendedDifferences: [
    { field: 'generation', before: 1, after: 2 },
    { field: 'target.source_revision', before: beforeRevision, after: afterRevision },
    { field: 'target.build_artifact_hash', before: beforeBuildHash, after: afterBuildHash },
    // Include each other actual target change, with its exact before/after value.
  ],
});
if (compared.comparison.status === 'MATCHED_EVIDENCE_ONLY') {
  await persistDerivedArtifacts(afterStore, compared.artifacts);
}
```

Both request byte hashes must match their canonical capture identities, and the full request must satisfy the TECH contract. All seven target fields may differ only when explicitly declared with exact before/after values. A changed request byte hash requires a strictly increasing generation. Registered experiment ID, physical subject UUIDs/setup, action IDs/order/parameters, assertion IDs/criteria, scopes, baseline, budgets, and rig remain exact.

Execution run/snapshot/capture IDs and absolute tick/frame intervals are retained independently and do not have to match. Actual camera/view/projection matrices, FOV, viewport, partial tick, capture stage, original human control state, perturbations, and invalidated assertions must match. Both captures require exact restoration evidence. Pixel integrity is verified before image comparison artifacts are produced.

A matched result creates a real four-row PNG (North A|B, East A|B, South A|B, West A|B) and a JSON comparison bundle. Structured changes and selected timelines retain separate before/after attribution. `MATCHED_EVIDENCE_ONLY` means setup/observation conditions matched; `acceptance` remains `NOT_EVALUATED`, and camera-affected behavior stays inconclusive. Mismatches return `NON_COMPARABLE` with reasons and produce no image artifacts.

## Portable source gates

Add this explicit test command as `test:visual-evidence`, and append `npm run test:visual-evidence` to the existing source CI chain when reconciling package.json:

```text
node --test debug-workspace/evidence/tests/visual-compiler.test.mjs debug-workspace/evidence/tests/visual-geometry.test.mjs debug-workspace/evidence/tests/visual-presentation.test.mjs debug-workspace/evidence/tests/visual-comparison.test.mjs debug-workspace/evidence/tests/visual-request-contract.test.mjs
```

The explicit paths work in Windows shells without glob expansion. Existing `npm run test:ci` is also required. The default `npm test` includes a browser/live palette test and is intentionally outside this source-only task.

Remaining live gates: pinned Forge/YSM capture geometry and visual verification, exact runtime restoration/observer-effect proof, a real MOD repair and matched replay, and the KNEEKURA-specific visual-format benchmark. No ID/depth diagnostic renderer, continuous full-resolution recording, or X8 same-frame multipass has been added. The default packet format remains provisional until the real-task benchmark is run.

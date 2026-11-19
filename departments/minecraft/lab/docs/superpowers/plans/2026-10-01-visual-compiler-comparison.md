# LAB Visual Compiler and Matched Comparison Implementation Plan

> Implement inline under the already approved experimental bridge design and source-only scope. Planning/TDD/review skills apply; live runtime, benchmark, publication, and PC operations remain deferred.

**Goal:** Compile immutable Cardinal-4 captures into independent human/AI presentations and compare genuinely matched repair runs.

**Architecture:** Resolve capture/timeline references through the existing EvidenceStore. Reuse its evidence cut, strict bridge JSON/material readers, and PNG utilities. Derived artifacts retain hashes and source Observation IDs; they never append or change canonical observations. Comparison consumes exact registered request bytes plus canonical capture evidence and preserves outcomes independently.

**Tech Stack:** Node.js ES modules, built-in node:test, existing PNG encode/decode.

**Spec:** TECH HUB `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md` (approved shared bridge design)

## Global Constraints
- Cardinal-4 is near-sequential, never same-frame.
- Complete captures require verified restoration; raw RGB remains immutable.
- Benchmark and real MOD repair acceptance require live evidence and are deferred.
- No new owner, canonical database, runner, network call, security change, or game launch.

## Review Focus
- Foreign/stale canonical references must fail closed; a free-standing restored boolean is not evidence.
- Malformed/oversized images and artifact path traversal must fail closed.
- Missing subjects or incomplete captures must not become complete spatial evidence.
- Render occlusion cannot be inferred from projected annotations.
- Legitimate build/generation and absolute tick differences must not conceal setup/control drift.

### Task 1: Compile canonical visual evidence
- [x] Write failing tests for four-quadrant image output, source/hash tampering, exact facts and labels, bounded drilldown, and unresolved checks.
- [x] Implement visual-compiler.mjs, visual-geometry.mjs, and visual-artifacts.mjs, reusing visual-capture.mjs from X3.
- [x] Verify node --test debug-workspace/evidence/tests/visual-compiler.test.mjs.

Interface: compileVisualPacket({store,sourceObservationId,visualChecks,timelineObservationIds}) -> {packet,artifacts}; persistVisualPacket({store,compiled}) writes only derived files. createVisualCrop({store,sourceObservationId,view,region}) -> derived crop with raw lineage.

### Task 2: Separate human presentation
- [x] Write failing tests for HumanNormal/HumanDebug/HumanEvidenceReview, strict shared identity, and unknown interaction rejection.
- [x] Implement visual-presentation.mjs pure presentation records and interaction classification.
- [x] Verify node --test debug-workspace/evidence/tests/visual-presentation.test.mjs.

Interface: createHumanPresentation({packet,mode,overlayIds,finding}) and classifyInteraction(type). No execution or canonical mutations.

### Task 3: Matched before/after evidence
- [x] Write failing tests for explicit intended target/generation changes, changed actions/setup/assertions/camera/baseline/restoration, and legitimate absolute tick changes.
- [x] Implement visual-comparison.mjs canonical comparison bundles and four derived side-by-side image rows.
- [x] Verify node --test debug-workspace/evidence/tests/visual-comparison.test.mjs; source CI suite; review diff and hand off exact hashes.

Interface: compareVisualRuns({before,after,intendedDifferences}), where each run is {store,sourceObservationId,requestBytes,timelineObservationIds}. Outcomes remain separate evidence and NEVER imply repair acceptance from image differences.

Final policy: exact registered experiment/action/assertion/physical subject identities remain setup gates. Execution run/snapshot/capture identities and absolute ticks are retained separately. Every changed target field requires exact declared before/after values, and any changed request bytes require a strictly increasing generation. The full TECH request semantic contract is validated before comparison.

Source gate: 55 visual tests plus existing source CI passed. No final independent approval or live Minecraft/benchmark acceptance is claimed.

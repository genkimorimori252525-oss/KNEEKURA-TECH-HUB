# Cardinal capture barrier and bounded trigger source plan

Scope: X3 and X5 source implementation on the reviewed LAB foundation, under the approved TECH HUB experimental runtime bridge design. Real editor/game launches and publication are separate gates.

## Contract and implementation choices

- One existing client and integrated server. Explicit owner installation and bounded requests only; default inert. No executable or camera script is accepted.
- Use the approved temporary camera fallback: a detached client camera entity, a transparent pausing screen and a bounded server-owner task rendezvous. Never move/add the player or add the camera entity to the world. Reject published servers, wrong world, foreign identity, active screens/input, non-idle Arena or stale epoch/revision.
- Record server pause, camera takeover, render eligibility and observer cost as perturbations. Affected behavior assertions become INCONCLUSIVE. Sequential frames never claim same-frame rendering.
- Capture scene pixels at Forge AFTER_LEVEL, before hand/HUD. Retain north/east/south/west transforms, projection/FOV/viewport, exact request/run/Arena/subject identities, observed server/client tick and frame ranges, immutable PNG hashes and missing-frame reasons.
- Restore exact original camera entity, camera type, options, screen and mouse capture state on success, timeout, identity drift and write failure. Restoration failure prevents COMPLETE. No replay after uncertainty.
- Reuse the existing evidence writer owner for asynchronous immutable image/row persistence. Use the existing Node ObservationRingBuffer, EvidenceRuntime and capture manifests for bounded opt-in trigger windows. No second scheduler or canonical store.
- Trigger pre-roll references only already retained observations/images. Missing past images are explicitly MISSING; no retrospective fabrication. Bounded future slots are advanced by the existing owner poll/tick, not an independent timer.

## Steps

1. Write pure protocol/state-machine tests: strict identity/rig/budgets; four ordered unique frames; timeout, stale identity, missing frames and exact restoration; then implement the pure Java capture session and barrier lifecycle.
2. Implement the real Forge adapter against inspected mapped 1.20.1 APIs. Add focused source/adapter tests; compile with cached actual Forge/Minecraft dependencies. Pure host test doubles prove control logic only, never Minecraft integration.
3. Add strict raw visual manifest and bounded trigger-window Node contracts with failing tests first. Preserve existing pre-roll manifests and canonical source references. Add source checks to the ordinary test chain.
4. Document exact X4/X6 interfaces, compile/test results and runtime limits. Produce an isolated diff and file hashes for integration/review. No runtime readiness claim follows from compilation.

## Integration seams

X2 owns Arena/action identity and its evidence writer update. This slice owns new capture classes and new Node visual/trigger modules. Coordinate any shared writer or Bootstrap hooks explicitly before merging. A BrokerEvidenceCut remains query coherence, never a pause proof.

X4 consumes immutable raw visual manifests/PNG references plus structured observations. X6 compares exact rig/camera/projection/viewport, experiment/setup/baseline/assertion identities, source observations and perturbation/restoration status. Neither may promote image existence or compilation to visual/gameplay PASS.

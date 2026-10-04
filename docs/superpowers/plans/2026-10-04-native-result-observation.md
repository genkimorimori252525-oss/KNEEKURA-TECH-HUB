# Native result observation implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` inline. This continues the user's already approved local execution architecture and standing authorization; keep the full original goal active until its remaining requirements are met.

**Goal:** Close missing result-observation channels and retain integrated native scenarios without promoting attempts, cancelled events or fixture state to successful gameplay results.

**Architecture:** Extend existing bounded `KneekuraDebugDecisionHooks.Session`, immutable evidence adapters and shared `SampledMotionTrace`. Use original-return callbacks and selected context; retain separate related-projectile identities only after exact source semantics and finite retention are established. No new observation database or gameplay visualization objects.

**Tech Stack:** Minecraft 1.20.1, Forge 47.2.0, Java 17, existing Node ESM consumers/tests.

**Spec:** `departments/minecraft/LOCAL-EXECUTION-HANDOFF-2026-10-02.md`; `departments/minecraft/vanilla-ai/REMAINING-EXECUTION-MATRIX-2026-10-04.md`; exact result research in `NATIVE-RESULT-HOOK-RESEARCH-2026-10-04.md`.

## Global constraints

- Baseline `1291b5e562982c851c8ce3d5c713ab87fd0a6056`, existing isolated `codex/minecraft-decision-native-20261003`, canonical LAB subtree only.
- Existing burst maximum 200 ticks /256 events /512 KiB and exact session/run/snapshot/process/Arena/UUID/selection-generation fences remain authoritative.
- Observation is OFF unless selected and explicitly armed. Never replay AI/search/eligibility or modify its budget/order.
- Original world and unrelated checkouts remain read-only; new private data is on C: due limited K: capacity. Native source freezes until clean stop.
- Preserve Draft, private evidence, missing channels and all original remaining requirements. No full-project completion from one slice.

## Review focus

1. False, cancelled or custom-overridden teleport must not create an explicit successful-teleport gap.
2. Callback in another selection revision/run/Arena must not split this subject's trace or enter its Decision result.
3. Multiple original callbacks within one sample interval, or callback at a sample tick, must retain evidence without creating duplicate/fabricated samples.
4. Projectile impact/hurt return/health loss are distinct; shielding, absorption, piercing and subclass dispatch must not become a false damage outcome.
5. Observer callbacks must remain finite/no replay even on sink failure, expired context, thread mismatch or identity retention limits.

## Task 1 — Original teleport return producer and typed consumer

**Files:**
- Modify `departments/minecraft/lab/debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugDecisionHooks.java`.
- Create matching `decisionmixin/KneekuraDebugLivingResultMixin.java`; register in existing `src/main/resources/kneekura-decision.mixins.json`.
- Modify `debug-workspace/evidence/original-decision-events.mjs`, `debug-workspace/evidence/debug-workspace-decision-adapter.mjs` and their existing tests.
- Extend `KneekuraDebugMotionTraceCache`, `KneekuraDebugMotionOverlayRuntime` and the existing pure cache test so native display also consumes a flushed successful callback as a gap, never a sampled position.
- Extend genuine Forge producer contracts with selected/excluded/thread/budget cases; no fixture call is native acceptance.

**Interfaces:**
- Consume original `LivingEntity.randomTeleport(DDDZ)Z` RETURN and its actual argument coordinates/boolean, existing `control` channel, `Session.matches` and `Session.record`.
- Produce `CONTROL_TELEPORT_RETURN` under the existing original-event schema. Data: `result` boolean; `requestedPosition` and `returnedPosition` each finite `{x,y,z}`; `dispatchScope='BASE_RANDOM_TELEPORT_RETURN'`; `reasonStatus='NOT_EXPOSED'`. Callback serializes after context/budget validation and never invokes teleport.
- Consume valid records as `RESULT` / `teleport_result`, with exact source observation IDs. Only `result=true` breaks the enclosing pair of retained SERVER points as `EXPLICIT_TELEPORT`; callback coordinates do not become samples.

- [ ] Write positive/negative/malformed and mixed-context retained tests; run the exact file and observe unsupported callback / unbroken short teleport fail.
- [ ] Add RETURN mixin and bounded producer callback; test selected subject, excluded channel, thread mismatch, exhausted context/budget and no replay using genuine APIs.
- [ ] Add strict typed consumer and trace boundary derivation; preserve false attempt as a result fact while keeping its trace connected.
- [ ] Run focused Node suite, portable/genuine Java source contracts and all actual bridge compilation. Expected: no failures; source/API proof distinguished from runtime hook proof.
- [ ] Commit the verified slice without publishing native-success claims.

## Task 2 — Original ranged-result relationship capture

**Files:** Existing Forge producer/lifecycle hooks and evidence adapters selected from exact method-body research; related tests and minimized research record.

**Interfaces:** Selected owner UUID plus explicitly observed projectile UUID/target UUID and existing immutable observation identities. Finite opt-in retention; original spawn/impact/result references preserve independent entity identities.

- [ ] Complete exact spawn/tick/impact/hurt/health-loss/subclass source-call research and define the smallest finite policy before edits.
- [ ] Write cancelled/failed/absorbed/removed/mixed-owner/mixed-context regressions and observe failure first.
- [ ] Instrument only original calls or authoritative post-result events; separate impact, return and HP effects. Do not change target selection to fabricate simultaneous traces.
- [ ] Run genuine Forge and focused consumer regressions; commit only proven source behavior.

## Task 3 — Native integrated acceptance and measurement

**Files:** Private trial drivers/fixtures/receipts outside Git, dated minimized acceptance/current handoff inside Git.

**Interfaces:** Frozen clean producer SHA, private copies of the preserved world, existing registered owner gates and finalized evidence stores.

- [ ] Prepare independent prelaunch conditions for Enderman teleport, Skeleton/Ghast ranged shot, damageable TF phases and Knight coordination. Retain original-save hashes and predecessor copies.
- [ ] Run finite trials; arm appropriate channels, retain actual source IDs and outcome receipts, and stop cleanly. No callbacks in constructors/load before arm count as selected capture.
- [ ] Show integrated Brain/pursuit/custom-flight/missing-capture diagnosis and explicit unavailable layers.
- [ ] Run same-initial-state paired observer-effect trials and authorized image checks; retain CPU/JFR/GPU/pixel coverage separately. Lack of capture capability remains an open item.

## Task 4 — Full remaining reconciliation and final gate

**Files:** Vanilla/FRONTIER research, requirement matrix, current handoff, tests and Draft PR80.

- [ ] Complete remaining per-algorithm semantic research, terrain/community/modern comparisons and source-established additional path/malus/control slices under the original constraints.
- [ ] Reconcile every original section21 criterion with specific evidence; do not close the goal while required work remains.
- [ ] Perform one fresh whole-diff review against baseline1291b5e; regrade by actual user impact and fix substantive findings in one RED→GREEN pass.
- [ ] Verify final exactHEAD focused/full suites, genuine Forge compile and hostedCI; publish Draft/update current handoff and report measured limits.

## Bounded custom-flight continuation — original Ghast reach return

Exact ANCHOR `Ghast$GhastMoveControl` class SHA256 `9cf70e9f2224e83c26b76de3ed734789c44e6e61d016550e443bea8b1de8934d`, normalized disassembly SHA256 `5602ddf2ea35d4692483668446b2d2b235611b8b3437dfa198f406a86893ec3d`, establishes a private `canReach(Vec3,int):boolean`. Its one inspected caller uses the normalized wanted-position displacement and `ceil(distance)` during original control tick. The method advances the Ghast bounding box for integer steps1 through length-1 and returns false at the first failed `Level.noCollision`; lengths0/1 return true without a collision-loop iteration. This is custom steering feasibility, not a complete A* search, exact collision location or final chosen destination.

- Reuse the existing explicitly armed `control` channel and its unchanged caps. Add one non-cancelling original private-method RETURN injection; never invoke/replay reach tests, collision queries, random, controller setters or movement.
- Retain exact selected Ghast/controller reference, cached UUID, owning server thread and full burst context. Record only actual direction argument, step count and boolean with explicit custom-steering scope; collision location and cause remain NOT_EXPOSED.
- Consumer accepts a strictly scoped `CONTROL_GHAST_REACH_RETURN` as direct EVALUATION / partial custom-flight reach capability. No invented CANDIDATE/SELECTION, destination, extra Motion sample or path frontier.
- First write genuine mapped producer owner/thread/OFF/channel/context/window/UUID/event/byte/sink tests and retained positive/false/malformed/identity/late-arm tests; preserve RED evidence. Then add the minimal hook/validator and integrate existing source suites. Genuine all-bridge/Mixin compile and Java/Gson→Node interop precede a fresh frozen private native trial.
- Preserve all prior producers and original world; native return/position correspondence is temporal unless stronger evidence exists. This slice does not complete Phantom/custom MOD controls, full flight diagnosis, all-view/GPU or the broad goal.

### Retained missing-capture display follow-through

R40 actual post-budget packet reports NOT_CAPTURED correctly. Controlled read-only omission of eight actual SERVER point inputs creates SOURCE_GAP40628..40673 while canonical bytes remain unchanged. Browser inspection shows the line break but no visible gap explanation before expanding raw JSON. Add a compact visible summary for the complete requested window: total gap count, at most four kind/tick/subject examples and omitted-detail notice. Keep cursor age expiry distinct from acquisition gaps, retain full source/provenance in existing details, and never claim a gap proves teleport or a zero count proves continuous acquisition. Write meaningful renderer RED→GREEN tests; then regenerate separate private artifacts without overwriting the first images/receipts and verify actual browser rendering.

## Bounded original open/closed heap-operation continuation

This continues Task4 and original sections5B4/8E4 without replacing the path recorder. Exact Forge ANCHOR PathFinder class `5d308818c953fcba2353de06b03fb4a80a0f12370c7f92f1baad7f7d574cae3b`, disassembly `d929f5154b88c5c977b99d47a7e0d8003a4d45373e08989b2b04711e8dc4f4aa`, has original inner insert calls at61/408, pop120, closed field write128 and changeCost380. BinaryHeap class is `05af3f22ca50b795799311c528044598e9e05974b56050929b4c5bcd8d808ff0`, disassembly `8648cc10e9147a1e58456630d4fb07e092f37445fce36cbd0f703f8d7218c8c3`. The actual profiler-bearing inner descriptor remains unchanged.

- Add only an explicit opt-in `frontier` channel; preserve default channels and200tick/256event/512KiB/node limits. Path-only and neighbors-only output remains unchanged. Use existing selected outer finder search/context rather than globally instrumenting every heap.
- Preserve each original virtual insert/pop/changeCost exactly once, including actual return/exception. Copy detached base Node fields only after the authority/channel/context/budget checks. Verify the passed heap is the finder's actual cached openSet reference. Never call search, distance/heuristic/evaluator, peek/size/getHeap, random or controller setters for observation.
- Distinguish start insertion, later accepted insertion/update and popped-before-caller-close. The inspected closed field write at128 is not a method return: do not relabel it as ORIGINAL_INVOCATION_RETURN_ONLY or add a field-write wrapper to this slice. Existing later neighbor/current-node and search-end cache flags remain separate state observations, with missing exact closed transitions explicitly unobserved. Do not infer rejection reasons from absent heap operations or equate popped with closed at the wrong boundary. Retain actual passed cost separately from g/h/f/costMalus and original return identity.
- If relating Node objects, use a finite per-search reference-identity table with explicit unknown/truncation at the limit; never treat equal coordinates or hash codes as unique object identity. Clear it on search begin/end and session/context teardown. Keep search IDs and source observation IDs; no complete frontier/path-cost claim from a capped stream.
- Write consumer positive/malformed/other-search/context/channel/partial-stream tests and genuine counting-heap tests first. Verify RED for missing hooks, then implement minimal wrappers/Mixin/strict consumer/optional drilldown and integrate existing suites. Java/Gson→Node interop and genuine all-bridge/Mixin compile precede a frozen private native trial. Preserve prior world/evidence and disclose callback conflicts/observer cost.
- Existing cache flags remain independently sampled search-end state. The new facts are original operation boundaries, not a complete pre-evaluator candidate population, reason trace, arbitrary MOD compatibility, final effective path cost or arrival result.

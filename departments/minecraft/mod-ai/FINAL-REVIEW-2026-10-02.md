# Final independent branch review — 2026-10-02

One fresh-context reviewer inspected LAB `4e834dc..135563f`, MOD `f9502df..53a84d0`, the acceptance plan/spec/ledger and actual images/comparison JSON. The reviewer did not edit source, operate the runtime or independently rerun source tests. Review outcome: **Critical0 / Important1 / Minor0**, conditional Draft publication after the fix and verification. General operation/merge readiness was not established. Final runtime/CI outcomes are recorded separately in the acceptance records.

## Important finding and one fix pass

`KneekuraDebugTankPresentation` exposed a cached View checked only on server ticks. `KneekuraDebugTankView` consumed it using only the Overworld dimension. A paused server could outlive the finite lease without clearing grid/brightness; disconnect or another connection could reuse stale presentation.

The fix publishes an immutable context containing the **original owner lease** issued/deadline nanoseconds and actual server reference. Both rendering consumers validate current singleplayer-server identity and monotonic elapsed time; owner uninstall clears the context. A render-tick transition requests the native `LightTexture.tick()` dirty-update path on activation/expiry, retaining pending invalidation across disconnect. This addresses the native lightmap cache as well as the grid. Genuine mapped LightTexture bytecode independently confirms tick marks `updateLightTexture` and update recomputes only when dirty. No owner deadline is recreated or extended; no server/game tick, action or capture budget is increased.

Regression was RED (missing lifecycle implementation), then GREEN: **30Tank checks**, including original19recipe checks and11current-context/deadline/clock-wrap/disconnect/foreign-server/finite-budget/lightmap-transition checks. Genuine Forge API compilation and writer3/image6/registered-world73 checks passed; comparison/capture43passed. The Windows portable owner suite reaches OwnerEnv5checks then fails its existing symlink privilege fixture; this remains a failure, with supported-platform aggregate checked by final hosted CI. There is no second review seat or automatic mutation retry.

## Behaviors considered and set aside, with executor rulings

The following review boundaries stand because the actual evidence supports their stated limited behavior. Their cost if misunderstood is an unsupported acceptance claim; the corresponding limitations remain in the records.

| Behavior | Review and executor ruling |
|---|---|
| Native capture clock/metadata | Both real renderer/Forge cache clocks held, actual event0required; raw values are not fabricated. |
| Exact restoration | Original values read before writes, partial writes tracked, bit-level readback; failure remains UNKNOWN, not restored PASS. |
| Strict comparison | Camera/time/perturbation/setup guards unchanged. Holding declares only generation/resource differences and remains evidence-only. |
| Capsule parser/ZIP | Canonical hash, integer/world/geometry/mode/UTF-8/entry/expanded-size bounds; no ZIP filesystem extraction or new traversal path. |
| Failed opt-in | Exceptions/mismatch disable presentation; no same-run retry or new mutation authority. |
| Presentation scope | Grid/lightmap only; no coordinator/resize/reset/YSM/server lighting/entity effects/physics migration. |
| Filesystem diagnostic | Bounded deepest class/reason improves diagnostics, adds no I/O or mutation retry. |
| MOD repair | Six-line missing item model follows existing sibling convention, original texture unchanged. |
| Visual scene interpretation | Eight scenes/holding pair visually inspected. Clipping AMBIGUOUS and north-arrow NOT_VISIBLE are justified; no forced positive. |
| UUID/numeric proofs | Structured native identity and registered artifact value are distinct from pixel segmentation/loaded transform proof. |
| Benchmark independence | Implementer evaluation is exploratory/unblinded. Reviewer provides independent qualitative inspection, not a blind accuracy benchmark; no independent accuracy claim. |
| Immutable evidence/timeline | Reviewer verified32raw hashes and8timelines preceding their capture writerSeq. Original seals/canonical bytes remain unchanged. |
| Native trigger window | Pre-roll MISSING,0ms +304ms,+500ms same-set reuse; PARTIAL/cleanupUNKNOWN preserved. Unloaded exit was not demonstrated. |
| Currentness/resume | Resource drift REVERIFY_REQUIRED/CURRENT_TARGET_CHANGED, no replay; UNKNOWN/INCONCLUSIVE and loaded proof limits preserved. |
| Input restoration | Minecraft API state readback only; physical devices/whole OS input state unproved. |
| Windows/stop/interruption | Failed/skip/startup results are not promoted. Old-Golden observations are not true-Tank trials. Interruption final result was pending at review. |
| Concurrent TECH work | Connector source/doc changes preserved, outside this runtime acceptance evidence. |

No minor findings were deferred. Record wording and source pins were finalization work, not additional source defects; exact-source publication and CI outcomes are recorded in the acceptance record. See [LIVE-REPAIR-ACCEPTANCE-2026-10-02.md](LIVE-REPAIR-ACCEPTANCE-2026-10-02.md) and [VISUAL-FORMAT-BENCHMARK-2026-10-02.md](VISUAL-FORMAT-BENCHMARK-2026-10-02.md) for final limits and results.

## Execution rulings retained from the ledger

| Order | Decision and reason | Cost if wrong |
|---|---|---|
|1|Use the original unmatched pair as diagnostic; hold both actual paused clocks instead of retrying for accidental equality.|Capture remains UNKNOWN if the real clock/restoration cannot be established.|
|2|Classify pre-READY native malloc as startup failure, constrain private heap3g and retain the failed attempt.|No second control success may be inferred from startup evidence.|
|3|Repair the discovered missing debug_force_takeoff model using its real sibling convention and unchanged texture; holding remains a separate gate.|Does not demonstrate an injected Blockbench defect or every visual defect.|
|4|Keep old-Golden Task1–3/30min results labelled; use a protected true-Tank copy for later image fixtures.|Those earlier results cannot establish native acceptance on the corrected world.|
|5|Port only g3 grid/lightmap behind an opt-in registered context; wholesale branch replacement would remove current TECH bridge paths.|Original resize/reset/YSM protocols remain untested.|
|6|Use finite READY600s after measured K prewarm, correct stale C registration to actual K world; owner stays120s.|Longer startup allowance is not a longer authorized operation lease.|
|7|Dispatch the one whole-branch review while the last finite startup attempt runs; final outcome records follow actual results.|The reviewer did not independently verify final interruption/CI outcomes.|
|8|After forced-main-rebuild diagnosis, use genuine precompiled MOD main output only after source/classes/resources/refmap hashes match; native LAB bridge/handshake still required.|Private procedure is not a general public launch feature or full loaded-target proof.|
|9|After an actual WindowsPowerShell thread-start failure, use a SHA-verified private copy of the existing PowerShell7 host for real CIM, preserving all PID/time/command guards and per-process-only PATH.|This later operator procedure was not independently rerun by the reviewer; standard WinPS5.1 readiness remains unproved, and any failed inspection still refuses operation.|

The seven original ledger rulings and the private startup refinements are retained; earlier failed trials remain immutable. Original C private clone is retained following automatic approval review rejection of the copy-plus-delete command; the approved safer copy-only path was used. The original review did not provide a detailed rejection reason. No deletion was retried.

Final implementer verification: r9 final LABf2d6165/MOD53a84d active native presentation/capture and intentional pending-wait stop passed, preserving UNKNOWN, closed-owner refusal, no replay, ACK31/drop0/queue0/VERIFIED_EXIT and TECH export/import. Exact-source hosted paired CI and complete TECH3141/332 passed at pin commit eb68b2d. Windows3fail/1skip and later private inspector/Gradle procedure retain their separate limits; no independent reviewer rerun of these final outcomes is implied.

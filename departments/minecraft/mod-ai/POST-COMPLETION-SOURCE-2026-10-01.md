# Post-completion implementation scope — 2026-10-01

Status: **BOUNDED SOURCE IMPLEMENTED; NATIVE OWNER/CAPTURE ROUND TRIP VERIFIED; FULL LIVE ACCEPTANCE OPEN.**

The user authorized the three retained Blockbench improvements and the saved LAB successor design, then explicitly prioritized code over real-device validation. The original MOD-AI and AI Usability Layer acceptance stays in its original records.

## Asset improvements

Partial-part repair, matched-camera before/after comparison, and separate UV/texture/display-slot adjustments are implemented. The [recorded editor trial](BLOCKBENCH-REPAIR-ACCEPTANCE-2026-10-01.md) binds the successful hosted run to TECH head `78785ed9723e2cdc569730d8c87eac745f88643f`. Geometry, UV and texture repairs have raw-image evidence; holding-display values have structural evidence. Actual in-game holding appearance was not tested.

## Saved LAB design

| Phase | Implemented source | Acceptance still open |
|---|---|---|
| X0 | Strict request/result, budgets, identity and UNKNOWN semantics | No live claim from a schema or hash |
| X1 | Exact request/assertion bytes, initial immutable RunSnapshot, existing-CAS import | Loaded target equivalence |
| X2 | Bounded real-API Arena, typed wait/block/teleport actions, one explicit cleanup reset, lease and journal fences | Actual reset/action/interruption/cleanup trial; use-item backend remains explicitly unsupported |
| X3 | One-client four-view capture, barrier, raw pixels, API-readback restoration, owner connection | Actual camera/restoration and perturbation trial |
| X4 | Contact sheets, crops, labels, exact schematic, independent AI packet, local human views; independent source review, retained-check validation and sealed derived export | Real visual-format benchmark; pre-seal writer trust is not compiler attestation |
| X5 | Explicit opt-in native Arena-exit event binding, bounded foreground watch, fixed capture slots, retained pre/post windows and exact source lineage in existing EvidenceRuntime | Real event-window coverage and timing; absent or ambiguous pre-roll stays missing |
| X6 | Matched identity/setup/camera comparison with raw/derived lineage; independent source review performed | Real matched before/after repair evidence |
| X7 | Explicit pinned local control, private finalized export/import, conservative TaskContext and retained resume | One real MOD repair/resume cycle and verified lesson |
| X8 | Conditional optimization remains DEFERRED | Select synchronized multipass only after a concrete sequential-capture limitation is observed |

The native owner consumes a separate hash-pinned operator registration. It verifies the actual parser/runtime PID, immutable input closure, already instantiated MOD/class-resource correspondence, and exact canonical disposable world. It installs the bounded owner on the existing server thread and coordinates capture on the existing client thread. It has no generic command execution, extra daemon, second evidence store or renewed lease.

A capture result cannot reopen mutation while restoration is uncertain. Shutdown waits for successful server detach and actual client capture quiescence before evidence sealing. Successful one-use cleanup closes the connection; its journal remains inspectable. Cleanup does not erase an earlier uncertain outcome.

Trigger watching is a separate explicit command with a sealed configuration and finite deadline. Ordinary status, planning and resume reads never arm it. The selected native event is an observed inside-to-outside transition of the registered subject; unknown or unloaded state clears the transition baseline. Captures consume the existing declared slots, and retention records their actual source timestamps. A later image cannot fill a negative pre-roll slot. The scoped result exporter still reports cleanup UNKNOWN and assertions INCONCLUSIVE or NOT_RUN; running a game alone cannot turn that projection into definitive repair acceptance.

See [scoped-control commands and limits](LAB-SCOPED-CONTROL.md), the [paired source interoperability gate](LAB-SCOPED-CONTROL-INTEROP.md), and the [original successor design](../../../docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md).

## Verification and publication boundary

The final local TECH source suite recorded 3,325 passed, 146 skipped and 8 warnings, with one environmental failure: `test_private_parent_validation_allows_real_external_directory`. Mandatory Git markers above the sandbox's writable directories prevent that fixture from constructing a directory outside every Git ancestor. The complete suite ran without exclusions; this failure is retained and is not reported as a pass.

LAB's source aggregate, portable Java owner contracts, genuine Forge API compilation, real writer tests, camera source checks and paired Python/Node control/export/import fixture are separate source gates. The paired fixture preserves UNKNOWN execution/cleanup, INCONCLUSIVE assertions and NOT_ESTABLISHED runtime attestation; it proves replay fencing even when TECH uses a fresh Store.

Independent X4/X6 source review has now been performed. It identified and resolved weaker retained-packet visual-check validation and post-finalization derived-image substitution; X6 had no additional finding. Pre-seal filesystem writer trust remains an explicit boundary rather than compiler attestation. Real Minecraft execution, the visual benchmark, full target/transformed-class/config/resource attestation and live repair acceptance remain unverified.

LAB source commits in this phase use `[skip ci]` to defer its Windows/self-hosted build and Thin Viewer gate without changing LAB workflows or runner settings. TECH's paired hosted workflow uses the exact [source pins](verification/lab-source-pin.json) for source checks, interoperability fixtures and pinned MOD compilation without launching Minecraft. Its earlier runs stopped at private checkout; the continuation below resolves that hosted source gate. Exact-head standalone hosted results are reported on the draft PR checks; skipped Windows gates are never counted as successful checks. No merge or deployment is included.

## Continuation review and restored integration CI

The local continuation and its independent findings are recorded in LAB's [source coverage record](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/b9d078a3b0a62669974f7384cd6401939a92941b/docs/KNEEKURA_EXPERIMENT_SOURCE_SCOPE_20261001.md). Initial fixes were published at LAB `39893cd432fec58c3e4567f8c7d5630deadbc522`; LAB `359e705e0925e742dff67d77c8af12fa6d8ca597` only updates that record. LAB `ba4a89e821850ee2dc406038db88f3a40f20fa49` additionally seals derived evidence before export. The source pin now selects `b9d078a3b0a62669974f7384cd6401939a92941b`, which includes the reviewed Windows directory-ID fallback and the live smoke record.

Retained visual answers now require valid distinct camera evidence, exact fields/semantics, unique check IDs and nonblank questions. Pending `NOT_RUN` checks still permit no evidence. The initial directory guard rejected null `fileKey`; the later Windows fallback reads volume serial plus a 128-bit object ID through Forge's existing JNA dependency. Read-only native handles reject non-directory/reparse inputs and fail closed on lookup/close/linkage failure. Creation time was experimentally shown to collide and is not a fallback. Native-ID lookup passed actual API and independent negative/handle-leak checks; it preserves the trusted local filesystem assumption and does not claim full target attestation.

With the user's standing continuation approval, LAB and MOD each received a separate read-only deploy key; TECH stores their private keys only in encrypted Actions secrets. The workflow keeps `contents: read`, disables persisted checkout credentials, and allows only those two secret references. The broad personal GitHub credential was not copied into CI. Temporary local private-key files were removed after both private checkouts succeeded.

At TECH `97513a4f371c15386663af1fb0eb1c09d36cc742`, [standalone run 36840268400](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268400) passed **3,140 tests**, skipped 332, with 8 warnings. [Integration source run 36840268482](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268482) passed the complete LAB aggregate, portable Java owner/camera checks, both real paired protocol fixtures, whole pinned MOD/Forge `1.20.1-47.2.0` compilation and genuine API checks. The visual suite passed 63/63 and Linux registered-world checks passed 7/7. This closes the former private-checkout permission blocker for source CI.

Local Windows verification remains separate: targeted regression 44/44, paired source protocol 1/1, API rejection regression and whole pinned MOD compilation passed; the full TECH run had 120 failures and 48 errors, and complete LAB/Java aggregates encountered symlink privilege failures. All Windows failures have not been classified. No exclusions or weakened symlink checks were used to manufacture success.

The additional LAB seal fix rejects a self-consistently rehashed packet/image added after finalization. Its existing inventory now covers hash-addressed derived files, and export requires that packet/ref hash inventory. Source schema and the 27-module registry are unchanged. Regression checks passed 75/75 and the paired fixture passed; independent reproduction confirmed the attack is refused and the original packet still exports. A review-found inventory bound bypass was also fixed and tested. Legacy seals without derived inventory cannot certify visual export, while nonvisual export remains available; historical seals are not rewritten. Pre-seal writer trust and compiler-origin proof remain distinct.

At TECH `928e3ccbb094d622eeda1982f202a4c141770197`, [integration run 36844126791](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36844126791) and [standalone run 36844126720](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36844126720) passed; standalone recorded 3,140 passed, 332 skipped and 8 warnings. These are the last completed hosted results before the Windows/native and MOD pin update below, not evidence for the new pins.

## Isolated live startup and observation smoke

The supplied Golden directory is an older production installation with MOD `2a1284f` / Forge 47.4.0 and a `simworld-golden-v1` save. A separately configured pinned source workspace used a copy named `KNEEKURA_DEBUG_WORLD`; the original Golden MOD, config and world were not changed. All 34 original world file hashes matched after the trial.

Actual client execution exposed two MOD problems missed by source compilation: uppercase texture/four sound paths failed before READY, then an ordinary network-probe helper inside the Mixin-owned package failed shortly after READY. [Draft MOD PR18](https://github.com/genkimorimori252525-oss/reimu-mod/pull/18) fixes these with case-only asset renames/references and an internal helper move. Asset bytes, sound event IDs, optional tracing gate/reflection/error handling and Mixin configuration are retained. The source pin selects MOD `f9502df842fc5f7103217217d7a327babe452843`. TDD regressions first failed; all 13 MOD JUnit tests passed, also independently. The hosted source workflow now runs those unit/resource regressions without starting a game.

The third local attempt at LAB `1264fdd` / MOD `f9502df` completed the existing G1/G2 smoke with exit 0 and both retained acceptance manifests reporting `PASS`. It observed the exact UUID declared in Golden's retained capture metadata, two heartbeat lanes and nine required entity lanes, retained a non-truncated one-second observation pre-roll, received clean flush ACK with zero writer drops/empty queue, and sealed `EVIDENCE_COMPLETE` after safe process stop. `requireReimu` was false. This is a short startup/observation/stop gate, not Reimu-specific behavior, Cardinal-4 pixels or full repair acceptance. LAB's reviewed Windows native regression passed writer 3, image 6, world 73; whole pinned MOD compilation and related Node 75/75 plus paired protocol 1/1 also passed locally. Separate Windows aggregate failures remain open.

Remaining gates are scoped owner installation/actions, camera restoration/observer effect, event timing, Arena reset/cleanup, matched repair/resume, the visual-format benchmark and production endurance/full target equivalence. The three PRs remain Draft. New-pin hosted results must be read from exact-head checks; the earlier successful runs cannot certify this update.

## Bounded native continuation

The preceding remaining-gate list describes the startup-smoke stage. At LAB `59ae068144a36fdaa6b6b6ef2e27c1ebd02de400` / MOD `f9502df842fc5f7103217217d7a327babe452843`, disposable-copy run `run-20261001115242-5bb8ac6edb07` subsequently completed with exit 0: exact-Reimu evidence, native owner installation, two actual four-view captures (eight 640x480 PNGs), exact API-readback restoration, verified 2-tick wait and yaw change, one-use bounded baseline reset, raw/derived packet retention, finalized export/import and clean process stop. All 69 evidence records are continuous across Arena epoch 0 to 1, with zero writer drops and `EVIDENCE_COMPLETE`. Original Golden save hashes remain unchanged, 34/34.

Live findings fixed in LAB were camera body/head-yaw mismatch, premature abort restoration readback and false producer sequence gaps after Arena/resource epoch changes. Existing tolerances, deadlines and real-gap/replay checks remain. Four regression tests join the normal G2/CI aggregate. Local related Node checks passed 79/79; genuine Forge checks passed writer 3/image 6/world 73; whole MOD compile and paired TECH/LAB fixture passed. Independent source review found no new issue. The previous failed/partial seals remain retained rather than rewritten.

Actual TECH profile/index/CAS preparation and its existing pinned 27-module registry drove the trial. Visual export manifest `997391b76326fd0ddaff505b0bbc5288c5034a2e527c1bdddca94f01c08c06fa` imported as `IMPORTED_LAB_REPORT`, result `b0707284a4201ea03f6aebc9485eee5795e349400f21dd5dd4d0358946c001c4`. Native cleanup verifies only `BOUNDED_BLOCKS_AND_SUBJECT_POSE`; the exporter deliberately retains cleanup UNKNOWN, assertions INCONCLUSIVE and runtime NOT_ESTABLISHED. Sequential camera takeover perturbs observation and invalidates `alive`.

Before/after comparison ran but returned `NON_COMPARABLE` / `NOT_EVALUATED` (`CAPTURE_CONDITIONS_MISMATCH:frames`). A subject-turn trial is not a matched MOD repair. Real matched repair/resume, event timing, the visual-format benchmark, in-game holding appearance, endurance/full target equivalence and separate Windows aggregate failures remain open. `use_item` remains unsupported. All three PRs remain Draft; this bounded trial is not full operational acceptance. Latest source-pin hosted checks must be verified at their exact TECH head.

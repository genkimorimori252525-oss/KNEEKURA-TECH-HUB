# Post-completion implementation scope — 2026-10-01

Status: **BOUNDED SOURCE STAGE IMPLEMENTED; LIVE ACCEPTANCE DEFERRED.**

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
| X4 | Contact sheets, crops, labels, exact schematic, independent AI packet, local human views; independent source review and retained-check fix | Real visual-format benchmark; derived-image writer provenance remains open |
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

Independent X4/X6 source review has now been performed. It identified and resolved weaker retained-packet visual-check validation; X6 had no additional finding. A separate derived-image writer trust concern remains open and prevents an unqualified independent-review pass. Real Minecraft execution, the visual benchmark, full target/transformed-class/config/resource attestation and live repair acceptance remain unverified.

LAB source commits in this phase use `[skip ci]` to defer its Windows/self-hosted build and Thin Viewer gate without changing LAB workflows or runner settings. TECH's paired hosted workflow uses the exact [source pins](verification/lab-source-pin.json) for source checks, interoperability fixtures and pinned MOD compilation without launching Minecraft. Its earlier runs stopped at private checkout; the continuation below resolves that hosted source gate. Exact-head standalone hosted results are reported on the draft PR checks; skipped Windows gates are never counted as successful checks. No merge or deployment is included.

## Continuation review and restored integration CI

The local continuation and its independent findings are recorded in LAB's [source coverage record](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/blob/359e705e0925e742dff67d77c8af12fa6d8ca597/docs/KNEEKURA_EXPERIMENT_SOURCE_SCOPE_20261001.md). Fixed implementation bytes were published at LAB `39893cd432fec58c3e4567f8c7d5630deadbc522`; LAB `359e705e0925e742dff67d77c8af12fa6d8ca597` only updates that record. The source pin now selects the latter.

Retained visual answers now require valid distinct camera evidence, exact fields/semantics, unique check IDs and nonblank questions. Pending `NOT_RUN` checks still permit no evidence. World owner installation now rejects directory providers without a non-null `fileKey`; creation time was experimentally shown to collide and is not a fallback. This makes native scoped owner control unavailable on the current Windows/JDK17 provider. It does not claim full target attestation.

With the user's standing continuation approval, LAB and MOD each received a separate read-only deploy key; TECH stores their private keys only in encrypted Actions secrets. The workflow keeps `contents: read`, disables persisted checkout credentials, and allows only those two secret references. The broad personal GitHub credential was not copied into CI. Temporary local private-key files were removed after both private checkouts succeeded.

At TECH `97513a4f371c15386663af1fb0eb1c09d36cc742`, [standalone run 36840268400](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268400) passed **3,140 tests**, skipped 332, with 8 warnings. [Integration source run 36840268482](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268482) passed the complete LAB aggregate, portable Java owner/camera checks, both real paired protocol fixtures, whole pinned MOD/Forge `1.20.1-47.2.0` compilation and genuine API checks. The visual suite passed 63/63 and Linux registered-world checks passed 7/7. This closes the former private-checkout permission blocker for source CI.

Local Windows verification remains separate: targeted regression 44/44, paired source protocol 1/1, API rejection regression and whole pinned MOD compilation passed; the full TECH run had 120 failures and 48 errors, and complete LAB/Java aggregates encountered symlink privilege failures. All Windows failures have not been classified. No exclusions or weakened symlink checks were used to manufacture success.

Remaining gates are the trusted-writer/derived-image provenance decision, real registered disposable-world execution, camera restoration/observer effect, event timing, reset/cleanup, matched repair/resume and the visual-format benchmark. No configured local runtime workspace or debug-world save was found in the documented setup locations. Source CI success does not establish any of these runtime gates. Both PRs remain Draft.

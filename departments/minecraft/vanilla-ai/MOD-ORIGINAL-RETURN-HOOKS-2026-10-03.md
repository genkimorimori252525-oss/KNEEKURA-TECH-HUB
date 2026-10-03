# Source-specific original MOD returns

This slice observes a pinned method's original RETURN and the cached state immediately afterwards. It never reruns a phase/formation setter, Hydra head update, decision method, sensor or path search. A method's return does not by itself prove that a stored value changed or explain the reason.

## Exact ANCHOR hooks

Minecraft 1.20.1 / Forge 47.2.0 / Twilight Forest 4.3.2508; actual mapped artifact SHA256 `7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a`. The [ten-class ledger](TF-ANCHOR-MAPPED-BYTECODE-LEDGER-2026-10-03.json) supplies exact member/body provenance alongside the pinned source correspondence recorded in the SDK research.

| Exact member | Actual return payload | Limit |
|---|---|---|
| `HydraHeadContainer.advanceHeadState()V` | Exact stored head container number and selected Hydra's cached head states | This method can return without changing state. `prevState` is not a captured invocation-entry value. |
| `SnowQueen.setCurrentPhase(SnowQueen$Phase)V` | Original enum argument and matching cached phase/counters | A setter can receive the current phase again; change/reason remains unknown. |
| `KnightPhantom.switchToFormation(KnightPhantom$Formation)V` | Original enum argument and matching local formation/clock | Local state does not establish group leadership or coordinated intent. |
| `UrGhast.setInTantrum(Z)V` | Original boolean argument and matching cached tantrum/custom-control state | This does not expose generated flight candidates or A-star behavior. |

Four non-cancellable, remap=false optional Pseudo Mixins are included only in the existing explicitly armed debug hook source set. Optional targets/injections permit absent MODs and unsupported members to stay unobserved; boot/annotation existence is not successful invocation capture. Actual records require exact selected object/server thread, source-compatible artifact/resources and finite budget. A foreign Hydra container is ignored before touching the selected budget. An unsupported source or cached layout cannot produce compatible facts.

## Request and retention

The explicit `mod` channel supplements the existing six Vanilla channels; existing default channel selection remains unchanged. Example:

```text
target <exact-uuid> --decision-burst --decision-channels mod --decision-ticks 100 --decision-events 64 --decision-bytes 262144 --decision-nodes 8
```

It still requires the launch's explicit Decision hooks flag. Every new selection resets the request. Existing maximum 200 ticks / 256 events / 512 KiB / 32 KiB event bounds and full session/run/snapshot/process/Arena/selection/UUID/dimension fences apply.

`kneekura.mod-decision-return/v1` preserves a separate `twilightforest:boss-original-return` descriptor; cached snapshot contracts and historical immutable records retain their original descriptor. Source resources are shared with the cached proof, while supported epistemic levels and instrumentation differ. World `returnTick` matches canonical gameTime. `returnLocalTick` is the separate last-completed server END observer counter used by the burst budget, explicitly marked as such; these clocks are not compared or substituted.

The retained SDK exposes `acceptsBurst`/`captureBurst`, requires exact source metadata, refuses duplicate event indices under different observation IDs and gives callbacks frozen compatible records. Packets retain at most eight recent MOD callback records, bounded facts/bytes and explicit input truncation. Each namespaced fact cites the original acquired observation ID. It records DIRECT_OBSERVED / DIRECT_RUNTIME_RELATION for the invoked method and cached post-state, while `stateChangeStatus` and `reasonStatus` remain NOT_EXPOSED. Labels remain derived presentation.

The common Decision Model maps these callbacks to EXECUTION and a `MOD_TRANSITION_METHOD_RETURN` timeline marker. `evidence-decision --channel mod_returns` reads canonical retained records without initializing/ingesting a finalized run. No SELECTION or complete transition history is invented.

## Verification status

Focused Motion/Decision contracts: 74 passed / 0 skipped. Portable Java request/descriptor checks, actual Java-to-Node descriptor equality, genuine Forge API contracts and all bridge/Mixin compilation passed. [Native original-return acceptance](NATIVE-MOD-RETURN-ACCEPTANCE-2026-10-03.md) captured Hydra64/Knight2, OFF/reset0, finite event/window stops, canonical924/drop0/cleanACK and read-only CLI/hash proof. Snow Queen/Ur-Ghast were NOT_CAPTURED in the NoAI fixture; full Boss battles and total observer effects are not claimed. The four-MOD native cached-state proof is separate.

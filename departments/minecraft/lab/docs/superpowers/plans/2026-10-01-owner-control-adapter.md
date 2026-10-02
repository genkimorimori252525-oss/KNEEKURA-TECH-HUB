# Registered scoped owner adapter and private result transport

This is the remaining X7 source connection in the approved experimental-runtime design. It consumes the Node-prepared immutable owner envelope and Java's concrete run-bound owner receipts. It does not launch a runtime or add a generic execution command.

## Fixed surface

- `owner-control-cli.mjs --owner OWNER_JSON --request COMMAND_JSON` accepts only inspect_owner, submit_action, request_capture, inspect_action export_result, request_cleanup and inspect_cleanup
- A separate TECH backend, `kneekura.lab.scoped-control.v1`, pins the executable, all 19 fixed source modules, owner config and owner envelope; the old read-only backend gains no implicit authority
- Command payloads select retained action IDs, finite capture slots or retained observation IDs. They cannot supply action arguments, camera parameters, paths, commands or executable names
- Action keys are SHA256 of canonical `{actionId,processEpoch,requestHash,runId,runSnapshotId}`. Capture keys use `{captureIndex,processEpoch,requestHash,runId,runSnapshotId}`
- Existing LAB action journals own ordering/replay state. Publication returns REQUESTED or uncertainty, never mutation completion. Fixed capture slots cannot be reused
- The in-JVM owner rechecks all authority/lease/world/material conditions before mutation. Node status is only a recent hint and is never a substitute for the JVM gate

## Implementation and tests

- [x] Pure retained-action selection: exact request identity, unchanged arguments, deterministic keys and expected revision derived from preceding mutations
- [x] Owner receipt/status verification: exact envelope/snapshot/world/material binding, bounded age, lease window, idle and safe state; no private values in public results
- [x] Atomic action/capture marker publication using fsynced temporary files and exclusive final names; duplicate or uncertain intents never receive a new key
- [x] Fixed CLI normalization with minimal reported statuses, explicit unestablished runtime attestation and no private paths/nonces
- [x] Finalized result export writes only private transport copies outside the sealed run; hashes bind every blob and the final manifest
- [x] Registered TECH invocation and complete inventory CAS import preserve UNKNOWN and suppress unsafe follow-up advice without adding a second replay ledger
- [x] Node↔Java and Node↔TECH source fixtures plus final local source checks verify the combined implementation; exact-head hosted full MOD compilation remains a separate publication gate

## Evidence and readiness

The two configured linkage tiers describe observed JAR/container/class-resource correspondence. Transformed class definitions and loaded config/resource equivalence remain unestablished. Only explicitly registered bounded diagnostic control is available; gameplay and visual acceptance stay inconclusive. Real runtime validation, the visual benchmark and real repair-cycle acceptance remain deferred by the user.


## Explicit cleanup addition

`request_cleanup` selects the existing single bounded owner reset allowance. It publishes only a fixed run/envelope/lease/revision marker; native owner code creates and owns the reset journal entry. `inspect_cleanup` reconciles that exact key without requiring current live status. A published marker without a native journal is `OUTCOME_UNKNOWN`, and a duplicate marker never dispatches again. The cleanup path may accept an idle unsafe owner with a still-valid lease; ordinary actions and captures cannot. A reset receipt does not erase prior experiment uncertainty or claim cleanup of unsupported state classes.

## Reviewed source checks

Independent Node review resolved export destination overlap in both directions, child names beginning with two dots, and original RunSnapshot integer-key canonical ordering. The combined Node source suite passed after those fixes and the explicit cleanup addition. A real paired Python/Node source fixture verifies registration, freshness, action/capture/cleanup intent, fresh-Store duplicate fencing, private export/import, unchanged sealed source bytes and conservative resume. All such outcomes remain source-only; native owner installation and actual world changes are unrun.


Final local integration checks: `npm run test:ci` passed; portable owner contracts passed53 Java checks plus the real-PID Node/Java closure fixture; combined23-class genuine Forge API compilation passed with16 writer/image/world checks. The independent owner review includes the terminal cleanup-close variant. One existing writer claim test was updated to select the image-aware three-argument queue record after X2/X3 integration; its original in-flight shutdown assertions remain intact. No Minecraft, live editor or user-computer runtime was started in this source phase.

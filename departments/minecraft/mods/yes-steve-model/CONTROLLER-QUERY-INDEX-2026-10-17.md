# Controller/query continuation index

Read only the dossier relevant to the current task. This connects the [earlier Java pipeline](JAVA-PIPELINE-INDEX-2026-10-17.md) and [state/query inputs](STATE-QUERY-INDEX-2026-10-17.md) to actual controller factories and predicates. The optional [evidence locator](EVIDENCE-LOCATOR-2026-10-17.md) searches known names without loading all snapshots or running audits.

## Follow the connection

1. [Client initialization](CLIENT-COMPAT-INITIALIZATION-RECOVERY-2026-10-17.md): declared client event, adapter calls before final native initialization, parser and command-hint lifetimes.
2. [Player controller assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md): model-resource discovery, per-entity factories, controller order, preview gates and name-map versus list behavior.
3. [Hybrid controller](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md): Bedrock state processing, builtin coded handoff, transition and active bone queue selection; ParCool as an integration case.
4. [Coded main predicate](PLAYER-MAIN-SELECTION-RECOVERY-2026-10-17.md): registered movement states and SlashBlade/TACZ/SWarfare override order.
5. [Hand predicates](HUMANOID-HAND-PREDICATES-RECOVERY-2026-10-17.md): hold PAUSE versus use STOP versus swing CONTINUE, hand-specific gates, conditional names and loop policy.
6. Existing [coded controller](CODED-CONTROLLER-STATE-RECOVERY-2026-10-17.md), [Bedrock controller](BEDROCK-CONTROLLER-RECOVERY-2026-10-17.md), [frame processor](ANIMATABLE-FRAME-RECOVERY-2026-10-17.md) and [Java render boundary](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md) continue toward queues/bones/renderer. Native model/render implementation remains unproven.

Related expression inputs:

- [ctrl priority/actions](CONTROL-PRIORITY-ACTIONS-RECOVERY-2026-10-17.md): cached first-match state names and setters into coded controller.
- [ctrl equipment/riding](CONTROL-EQUIPMENT-PREDICATES-RECOVERY-2026-10-17.md): raw item slots, prefix matching, classifier and actual action-guard precision.
- [Maid query adapter](MAID-QUERY-ADAPTER-RECOVERY-2026-10-17.md): absent provider versus wrong entity versus active maid defaults/types.
- [Utility/noise/debug](UTILITY-NOISE-DEBUG-RECOVERY-2026-10-17.md): local metadata, block-name matching, debug output and native noise call boundary.

## Distinctions that prevent incorrect reuse

- ctrl movement-state query is not a read of coded main's current selected clip: it has separate input sampling/cache, and walk's sign test differs.
- A selected compatibility animator name does not imply the model has the corresponding clip.
- A controller discovery can run even when its per-entity factory will be suppressed by a preview condition.
- A name in a controller/event map is not always a nonempty animation clip; parallel discovery has explicit overwrite order.
- A hybrid is not simultaneous output of two controller queues: activeController chooses which queues are visited.
- ctrl.swing/use accept a hand slot but their condition callbacks ignore hand; coded hand predicates compare the actual active hand.
- Hand PLAY_ONCE/LOOP call arguments may be omitted by the format-aware compatibility helper.
- Static conditional cache/missing-clip concerns are not reproduced bugs and do not authorize guessed upstream patches.

## One scoped batch checkpoint

[CONTROLLER-QUERY-CHECKPOINT-2026-10-17.json](CONTROLLER-QUERY-CHECKPOINT-2026-10-17.json) records exactly nine new cohorts, all passing, in approximately1.792seconds on the recording environment. It runs Python static auditors only, checking exact artifact/source anchors and negative integrity controls. There were zero duplicate member keys among these nine cohort sets, so zero overlap comparisons; this is not an independent cross-cohort semantic review. Earlier supporting snapshots and all other repository code were not globally rerun. The earlier fixed17 and fixed10 checkpoints are unchanged.

Central map remains669 rows and byte-identical. Captured declarations include constructors, lambdas, abstract methods and support, so their counts must not be presented as new semantic mappings or completion percentage. Independent semantic review for these nine cohorts is NOT_RUN. Minecraft/Forge, native providers, packets and whole-project CI were not executed.

Continue through remaining conditional swing/use/vehicle/armor predicates and compatibility adapters as needed. Keep direct Java evidence, source hints and external-provider behavior separate. This checkpoint is not a whole-target completion claim.

## Added after that fixed checkpoint

These dossiers have their own scoped receipts; they are not included in the nine-cohort batch above:

- [Conditional model-name ingestion](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md): actual lambda-handle producer, default-animation sharing and tag priority provenance.
- [Humanoid riding/armor](RIDING-ARMOR-PREDICATES-RECOVERY-2026-10-17.md): ordered provider/legacy fallbacks and first-passenger/type-ID boundaries.
- [First-person arm assembly](FIRST-PERSON-ARM-ASSEMBLY-RECOVERY-2026-10-17.md): separate animation/condition map with shared resources, and isolated JDK regex contract.
- [Vehicle/projectile entity controllers](VEHICLE-PROJECTILE-CONTROLLERS-RECOVERY-2026-10-17.md): state selection, literal fly/air discrepancy, aircraft-origin rotation queue.
- [Extra/GUI preview controllers](EXTRA-PREVIEW-CONTROLLERS-RECOVERY-2026-10-17.md): cap lifecycle, hover/focus emission timing and sound cleanup scope.

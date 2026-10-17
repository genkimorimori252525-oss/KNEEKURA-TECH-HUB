# Expression requests and roaming values use distinct routes

This optional task guide joins existing exact-artifact dossiers. It is not a new runtime test, mapping promotion, startup audit or guarantee of synchronization. Target: YSM2.6.5 Forge1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. New joins are PRIMARY_STATIC_REVIEW_ONLY; independent review NOT_RUN.

## Question: does suppressing a roaming expression packet suppress every state update?

Not necessarily. The GUI's expression relay and the local roaming-change drain are different Java paths. Neither is a delivery guarantee.

1. [Roulette forms](ROULETTE-EXPRESSION-UI-RECOVERY-2026-10-17.md) parse and enqueue locally before their optional SubmitRouletteConfig branch. A lexical roaming-only match skips that expression packet branch, not the prior local queueing.
2. [Processor tasks](ANIMATION-PROCESSOR-RECOVERY-2026-10-16.md) execute selected queued expressions at their pre/post phases. Enqueue alone does not establish that a later frame reaches evaluation. Model clearing discards pending tasks. Preserve that dossier's IValue error-handling counterevidence; a nullable callback is not evidence of a reproduced failure.
3. [Local roaming storage](STRUCT-COPY-CHANGE-RECOVERY-2026-10-17.md) writes float values separately from dirty/change bookkeeping. Equal old/new values and the existing-name-set limit can prevent change recording. A valid assignment is not synonymous with a pending delta.
4. [Client tick](RENDER-SELECTION-RECOVERY-2026-10-17.md) reaches the player change handler only after the available/non-END gates, manager service calls, refresh-rate query and nonnull player/capability. Prior exceptions can prevent that invocation; this is not a guaranteed per-frame flush.
5. [Outgoing changes](POOLED-NAME-CHANGE-CODEC-RECOVERY-2026-10-17.md) require local player, nonzero current model hash, LocalRoamingStruct and dirty state. They pop the accumulator, propagate to the eligible vehicle, convert pooled names to strings and request SubmitRoamingVarsChanges. This producer has no LOW_BANDWIDTH_USAGE test in the inspected body; later server staging has its own bandwidth conditions.
6. [Packet handling](ANIMATION-PACKET-ROUTING-RECOVERY-2026-10-17.md) and [remote storage](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md) apply their own side, target, model/readiness and local/remote rules. The maid branch is a recorded no-op, not player synchronization inherited automatically.

Thus expression-text retransmission and value-delta transfer must remain separate in a reusable design. Do not infer that every GUI expression is forwarded, every local assignment becomes a delta, or every handled delta becomes a visible animation.

## New joined boundary: drain precedes the shared channel guard

The outgoing player method pops/reset-clears its dirty accumulator before calling NetworkHandler.sendToServer. The [shared helper](ANIMATION-PACKET-ROUTING-RECOVERY-2026-10-17.md) returns without sending if its exact channel-version presence check fails. The player body has no acknowledgement-dependent rollback/requeue around this call.

Consequently this local drain is not transactional with successful transmission: a normal no-send return can follow a completed local pop on the inspected path. This is a composition of the captured call order and helper guard, not a measured lost update. Later writes, reinitialization or other synchronization may supply state; no claim that all recovery is absent follows. Reuse code should state whether it wants best-effort transfer, retry ownership or acknowledged delivery rather than infer reliability from the method name.

## Results are strings, then form-specific conversions

The processor formats successful strings with quote characters, null as the literal `null`, and other values with toString before invoking a result callback. The screen's initial form queries enqueue client-executor work from that callback.

The captured screen transformNumber compares literal `null` first (returns0), otherwise asks NumberUtils.isParsable before Float.parseFloat, then asks BooleanUtils.toBooleanObject and toBoolean, otherwise returns0. Its method has no local exception handler. This report does not replace the external Apache conversion predicates with a guessed grammar. Checkbox state tests the resulting float greater than0; radio selection uses Math.round; range construction forwards it to the slider.

These are presentation conversions after expression evaluation, not changes to the Molang value type system. The local and remote expression receivers also need not evaluate at the same frame, context or state. Deterministic cross-client outcomes have not been demonstrated.

## Minimal evidence to read for a task

- Implementing local form controls: roulette UI, processor queue and value conversion branches.
- Reusing change tracking: struct change bookkeeping, outgoing name conversion and shared channel guard.
- Reusing a relay: command/relay producer and packet routing; do not transfer one emitter's permission predicate to another.
- Applying remote state: entity-load application, roaming merge and server property staging, preserving full/delta distinctions.

Use the one-file member viewer for an exact method instead of loading every linked snapshot. Existing frozen checkpoint receipts remain historical; this guide does not relabel them as a complete transport test.

## Projectile and vehicle capability transport extension

[Projectile owner-state transport](PROJECTILE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) and [vehicle transfer](VEHICLE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) close the next Java-side branch: retained server maps, deferred versus optional-only producers, NBT/string-pool wire conversion, explicit lazy initialization and later processor installation. A queued callback is not a frozen launch snapshot; wrapper capability presence is not rendering readiness. The fixed8 [checkpoint](ENTITY-CAPABILITY-TRANSPORT-CHECKPOINT-2026-10-17.json) joins these two cohorts with six existing anchors, without changing older manifests or promoting the central map.

## Client-local command and debug-target extension

[Client Molang/watch commands](CLIENT-COMMAND-DEBUG-TARGET-RECOVERY-2026-10-17.md) join command returns, queue submission, static watch ownership, weak target attachment, explicit lazy-provider queries and result display. Integer1 is not evaluation success; watch editing guarded by a local capability can still observe an active nonlocal target. Switching target retains shared watch configuration. The separate fixed8 [checkpoint](CLIENT-COMMAND-DEBUG-CHECKPOINT-2026-10-17.json) checks these connected boundaries without executing the target or promoting mappings.

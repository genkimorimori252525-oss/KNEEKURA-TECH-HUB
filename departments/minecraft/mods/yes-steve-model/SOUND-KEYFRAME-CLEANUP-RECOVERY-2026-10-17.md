# Sound keyframes, reset and cleanup callers

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.Eight declarations across SoundKeyframeExecutor and generic event-keyframe support;55 integrity checks/7 negative controls. Separate955-class scan of manager stop/trim and executor reset/stop finds10 direct calls in10 methods,0 bootstrap handles (2 checks/6 negative controls). Not reflective/native/external closure; no playback, target execution, mapping promotion or independent semantic review.

## Cursor consumption is separate from emission

SoundKeyframeExecutor `O00OoO0oOoO0oOo0o000ooo0` retains the supplied list and manager directly. It neither copies nor sorts the list. executeTo repeatedly reads the next keyframe and returns if that start tick is greater than current tick. Otherwise it increments nextIndex BEFORE checking allowEmitting and null/empty sound text. A suppressed/empty event is still consumed; a later enabled call does not revisit it unless reset occurs.

An eligible event calls playSound with ID0, force=false and no configure callback, then discards the boolean. Failure to create/dispatch sound therefore does not rewind the cursor, and a thrown playback/configuration error occurs after cursor advancement. No per-call maximum bounds the scan besides the current list end. Ordering/immutability of the provided list is a producer contract, not guaranteed by this executor.

reset first sets cursor0 then calls manager.stopAll. stopAll only calls the manager and preserves cursor. These methods are not aliases. A cleanup exception after cursor reset can leave that changed cursor alongside incomplete stop operations.

## Exact cleanup call routes

The [caller inventory](SOUND-CLEANUP-CALLERS-EVIDENCE-2026-10-17.json) retains full bodies and offsets:

- Bedrock controller transition calls its context manager stopAll at19, after its both-states-null early return and before onExit/onEntry processing. Later exit/entry expressions may themselves emit new effects; this call is not a guarantee the entire transition ends silent.
- Bedrock clear calls context stopAll at100 after clearing player/list state on the normal path.
- AnimationPlayer resetEventKeyframes calls sound executor.reset at51 after instruction-keyframe completion/reset; resetToIdle calls reset at28 only when not already IDLE; stopPlayingSounds calls executor.stopAll at11 when nonnull.
- AnimationProcessor tick path calls GLOBAL manager.trim at53, while clearModel calls GLOBAL stopAll at47 after preceding model/memory/task resets.
- SoundFunction.StopAll calls the selected manager at68, after its separately documented emission/manager-selection gates.
- The remaining two direct calls are the sound executor's reset and stopAll delegations.

This inventory directly contains the relevant earlier controller/player/processor bodies; no new promotion of those existing mappings is claimed. The fixed scan found no other direct or bootstrap trim target calls; do not extend that to external/native code or universal runtime reachability.

## StopAll is an ordered request sequence, not transactional close

The existing manager body requests stop on named instances, then unnamed instances, then clears both collections. No local per-instance catch/finally makes the entire operation atomic. The [sound-instance dossier](SOUND-INSTANCE-LIFETIME-RECOVERY-2026-10-17.md) distinguishes inherited stopped flag, submitted engine-stop callback and stream close. A failure before collection clears can leave retained entries; a completed Java stop request is not immediate audible silence or guaranteed decoder retirement.

Trim removes already-stopped entries; CustomSoundInstance.isStopped can itself request engine stop when observing a closed stream. Thus trimming is not necessarily a pure collection operation. Only the global manager's processor trim call is proven by this target scan; animation/controller manager cleanup follows their reset/transition paths.

The AnimationContext reset body separately runs deferred expressions and clears variable storage; it is not itself one of these direct sound-stop calls. Finalizing context can emit effects, so sound cleanup and deferred-expression ordering must be composed from the specific caller rather than inferred from a generic reset name.

## Reuse

Preserve cursor consumption, event ordering, selected manager scope, reset versus stop behavior and ordinary-path exception boundaries. This joins the sound lifecycle to animation changes without testing an audio engine. Added after the fixed sound-lifecycle checkpoint; next inspect only missing cleanup ownership questions or a genuinely uncovered Java dependency, not repeat existing controller state machines.

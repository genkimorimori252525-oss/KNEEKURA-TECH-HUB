# Synchronization state consumers: model screen and loading overlay

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.Eight selected declarations across two consumers and two generated switch tables;63 integrity checks/9 negative controls. PlayerModelScreen capture is limited to state text and two model-map callbacks; the whole screen is not semantically analyzed. No UI rendering/runtime, independent semantic review or mapping promotion.

## Polling state differs from receiving a progression callback

PlayerModelScreen `O0o0oOO0OOO0O0OooOooOo0o` reads ClientModelManager.getSyncState each time its selected state-text method runs. WAITING/LOADING/PREPARING select corresponding labels. SYNCING with received0 selects a syncing label; otherwise it formats received/total. Other switch outcomes, including IDLE, return without this text.

The class declares the two model-map listener callbacks onAlterModels and onNewModelLoaded, each invoking init and ignoring its supplied map parameter. It declares no onSyncProgression override in the retained owner declaration; the interface's corresponding default body is empty. This does not establish all external listeners, but it prevents treating the manager's terminal callback arguments as automatically displayed by this screen.

## Loading overlay uses a different post-sync measure

LoadingStateScreen `Ooo0oooO0o0O0oO0oOOOooO0` returns if its disable option is true. Otherwise it reads state after calculating configured layout. In IDLE it separately queries new-model queue size. Positive queue size displays a loading-models message with queue size and current model-map size plus queue size; its bar uses modelMapSize/(modelMapSize+queueSize). Zero/nonpositive queue size returns without that overlay block.

The numerator is the size of the entire current map, not a counter of successfully loaded models in just this sync session. The queue count is an independently sampled queue size. Neither is GPU/upload completion, and no atomic snapshot combines them. Under the ordinary nonnegative sizes and positive queue gate the denominator is positive, but integer overflow/external mutation are not proven impossible by these bodies.

Outside IDLE, WAITING/LOADING/PREPARING select messages; SYNCING received0 selects a message without a progress bar. With received nonzero the bar computes float(received)/total and truncates width150*ratio to integer. There is no local clamp to[0,1] or positive-total validation in that branch. The manager normally establishes positive total when entering SYNCING through preparation; arbitrary state mutation or external invocation requires separate evidence before calling this a bug.

## Consequence for the terminal-count finding

The [manager](CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md) can reset total to-1 before invoking its terminal progression listener. These two UI consumers poll type/counters instead of directly rendering those callback arguments. On ordinary transition to IDLE, the model screen skips state text and the overlay switches to its queue/map measure. Therefore a terminal(-1,complete) callback does not by itself prove a displayed negative denominator or broken bar. No screenshot or runtime symptom was claimed and no display patch was made.

Generated switch tables are retained to disambiguate obfuscated enum fields. Event registration, actual draw frequency, screen init internals and external observers remain outside this bounded cohort. This closes the immediate Java consumer question while preserving the distinction between protocol progress, Java model publication and visible rendering.

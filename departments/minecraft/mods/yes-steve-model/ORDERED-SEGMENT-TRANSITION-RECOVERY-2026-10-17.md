# Ordered segment cursor and segmented blend transition

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.13 declarations across searcher, segmented transition and segment data;84 integrity checks/11 negative controls. Separate955-class scan:9 direct calls in7 methods,0 bootstrap target handles (2 checks/6 negatives). No target/native execution, independent semantic review or mapping promotion.

## Stateful search, not a binary search over a validated immutable table

Searcher `oOOOO0oo00o0oOoo0oOoooOO` retains the supplied list/getter, reads last and first entries during construction, initializes cursor0, and validates only leftBound<=firstRight<=lastRight (plus leftBound<=lastRight). Empty list has no explicit accepted case; intermediate ordering is not fully checked at construction. The overall right bound is cached from the last entry, while later scans call the getter again. No defensive copy, NaN/finite validation or synchronization is present.

A one-element list always returns its element. For multiple elements, a point below currentLeft returns/resets to the first segment and may recurse from there. A point equal to currentLeft, below currentRight, OR a currentRight equal to overall rightBound returns the current segment. Only after these tests does point>=overallRight select the last segment. Consequently equal final boundaries can cause an earlier current segment with that same right boundary to satisfy the terminal shortcut; do not assume a universal last-element rule independent of cursor history.

Otherwise it scans forward from currentIndex+1, checking each visited left<=right and selecting the first right strictly greater than point. It has no explicit list-size termination in that scan; valid ordered finite data and point/bound comparisons are its implicit prerequisites. Unsorted interior bounds can throw when visited, not necessarily on construction. An earlier boundary, duplicate boundary, endpoint or invalid input should not be normalized to another search algorithm without an explicit reuse decision.

## Transition arrays and units

SegmentedBlendTransition `o0o00oo00Oo0oo00ooOO0ooo` builds time.length-1 segments. It multiplies each supplied adjacent time by20 and stores positions as1-suppliedPosition. It does not separately validate matching array lengths, minimum two times, finite values or full monotonic order; array/list/searcher operations impose their own failures. More positions than needed are not read.

Each segment retains start/end tick, end-minus-start total, complemented start position and complemented-end-minus-start delta. get(tick) uses the searcher; tick<=start returns start position, tick>=end returns start+delta, otherwise it linearly interpolates. There is no value clamp to[0,1]. length returns the searcher's cached final bound, i.e. the multiplied time domain. Preserve the [player's existing transition unit findings](ANIMATION-PLAYER-CLOCK-RECOVERY-2026-10-17.md) rather than silently compensating factors or assuming native input units.

startNew constructs a new transition/search cursor over the same segment list. It is an independent cursor, not a deep copy of segment data. This differs from IBlendTransition's default return-this and the stateless linear implementation documented earlier.

## Exact Java callers and external boundary

[ORDERED-SEGMENT-CALLERS-EVIDENCE-2026-10-17.json](ORDERED-SEGMENT-CALLERS-EVIDENCE-2026-10-17.json) identifies two player point-producer search calls, three BoneAnimationQueue searcher constructions, two segmented-transition searcher constructions, one transition search call and the searcher's own recursive call. It finds no direct/bootstrap Java invocation of the float-array segmented-transition constructor in the fixed955 classes. The source marks that constructor Native Access; absent Java calls does not prove it unused or establish native input validity.

The queue's known source-layout divergence is preserved; these exact caller descriptors do not rename or promote its existing role. Together the snapshots connect search cursor lifetime to existing keyframe point and transition consumers. This is later than all prior frozen checkpoints and does not silently extend their receipts.

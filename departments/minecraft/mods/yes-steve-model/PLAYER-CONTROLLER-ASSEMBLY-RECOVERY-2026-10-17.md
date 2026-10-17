# Player controller discovery and assembly

PRIMARY_STATIC_REVIEW_ONLY. Exact 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Seventy-eight declarations across ten owners including abstract factory/resource interfaces, with no invented Code for declarations. No mapping promotion, independent semantic review or target execution.

## Two-stage construction

PlayerControllerCollection (`o00oOOo0o0ooOo0oO0o00Ooo`) initializes a static discovery collection only when build sees it empty. AnimationControllerCollection (`OoO0O0o0OOOOO0O00o00OoO0`) first processes discoveries against model/assets into a captured list of factories. The returned Consumer later calls those factories for an animatable and feeds their controllers to addAnimationController in list order. Thus resource-name discovery occurs at build time, while per-entity construction and GUI conditions occur when the Consumer is invoked. It is not continuous rediscovery every animation tick.

withCondition on ControllerDiscovery (`o0OOOO0oO0O0oo0Ooo0Oo0oO`) still processes the underlying discovery first; it gates factory.create later. A false preview condition does not imply discovery work was skipped. Factory/resource interfaces are contracts only. The Player adapter reads model controller/animation maps and conditionManager armor conditions; it does not merge a second animation map from CommonAsset.

## Declared discovery order

Base category is `player`, with this registration sequence:

pre_parallel → optional parcool → vehicle → pre_main → main → post_main → pre_hold → hold_offhand → hold_mainhand → post_hold → optional fire → pre_swing → swing → post_swing → pre_use → use → post_use → passenger → optional carry_on → cap → gui_hover → gui_focus → parallel → armor.

ParCool and CarryOn factories are inserted via Optional.ifPresent; fire depends on GunFirePredicate.available. These conditions are evaluated during lazy collection initialization, not independently on every later build. The resulting number of controllers is not a fixed 24: discovery expands named resources and optional/preview conditions alter output.

Simple discovery always constructs its named controller when invoked, except GUI-only names which require IPreviewEntity. It does not first require a matching clip. cap/gui_hover/gui_focus use CodedAnimationController directly. Most other built-ins use HybridAnimationController; pre/post multi slots use EmptyPredicate. Final parallel sets the legacy blendRotation constructor argument true; pre_parallel uses the ordinary constructor. Construction order is not itself proof of final visual dominance/blending; refer to [hybrid dispatch](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md) and [frame processing](ANIMATABLE-FRAME-RECOVERY-2026-10-17.md).

## Multi discovery

`O0ooO0o0O0O0ooooOO0o00OO` matches model controller names against `^category\.pattern(_.+){0,1}$` and event names against `^category_ctrl_pattern(_.+){0,1}$`, using asMatchPredicate. The supplied category/pattern strings are formatted as regex fragments, not Pattern.quote escaped. Events replace `_ctrl_` with `.` (String.replace, all occurrences). Matching names enter an ObjectRBTreeSet, deduplicating and sorting by String order, then construct controllers in that order. Numeric-looking suffixes are not numerically sorted.

## Parallel discovery and precedence

`OoO0o0ooOO0ooOo0oO0oOOoo` builds an Object2ReferenceRBTreeMap from controller name to optional animation name in three passes:

1. Matching model controllers insert name→null.
2. Matching event names convert `_ctrl_` to `.`. Parse the suffix as integer; 0–7 with corresponding animation key present stores that original suffix's animation name, otherwise null. Only NumberFormatException is caught (range39–115→119 in the event lambda); containsKey here does not test clip isEmpty. Leading-zero/plus-form integer text is not normalized before constructing the animation name.
3. Nonempty animation clips with names exactly `name[0-7]` insert/overwrite canonical category.name_digit entries.

The tree map then emits one controller per key in String order. Later passes can overwrite an earlier value for the same key; they do not add duplicate instances for that key. In multi=true mode controller/event names allow arbitrary nonempty suffixes, while automatic clip-name discovery still only accepts one digit0–7. Player's parallel helper passes multi=true. In multi=false mode controller/event regexes are also restricted to one digit0–7. The name `parallel` does not establish execution on multiple threads.

## Armor and single discovery

Armor (`OoOO00oOOooOOOo0OooO0000`) iterates every EquipmentSlot enum value. An explicit controller or event key qualifies any slot, including hand slots; only the fallback condition/default-animation branch requires Type.ARMOR. Fallback checks condition.hasTest or existence of `slot:default`, not clip nonemptiness. The returned factory suppresses all these controllers for IPreviewEntity. Each slot is added at most once by the ordered continue branches.

Single (`OO0oOo000oo0O0ooO0oOOoOo`) accepts a controller key only when its hybrid flag is true; otherwise/next accepts an event key; otherwise any named non-null, nonempty clip qualifies. Rejection returns a no-op factory. The private player single helper is captured as support but not invoked by the displayed player init sequence; this is not a whole-repository no-call claim.

## Existing animation-manager lookup join

Reusing the already captured AnimationData owner `Oo0OO00OooO0o0OOOo0oO0Oo` in ANIMATABLE-FRAME-EVIDENCE (not adding it to this cohort's 78 declarations): addAnimationController only appends to the list. The name map is populated lazily only when it is empty and the list nonempty; map.put means later duplicate names win lookup while the list still retains both entries. Later additions do not invalidate an already populated map in this method. reset calls each controller.clear then clears list and map on normal completion. These are distinct list/lookup contracts, not evidence that duplicate or late additions actually occur in normal initialization. Preserve build-before-first-lookup ordering when adapting this assembly.

## Reuse

Preserve resource-discovery time versus entity-construction time, ordered/lexical deduplication, event-versus-clip presence tests, and preview guards. Do not flatten all discoveries into unconditional controller construction or infer that every named controller has a usable clip. A source-level null/empty distinction is not a reproduced user-visible bug. The scoped auditor checks exact snapshot integrity and negative missing-body controls; abstract entries remain declarations only.

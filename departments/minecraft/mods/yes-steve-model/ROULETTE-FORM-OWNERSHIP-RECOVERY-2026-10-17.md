# Roulette form inputs and selection lifecycle

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. New evidence contains17 declarations/five owners,112 integrity checks/ten negative controls. Screen selection bodies reuse the earlier53-declaration roulette UI evidence; no duplicate snapshot or confidence promotion. No GUI/game/native model decoder was run.

## Data carriers do not validate a form schema

- ConfigForms `O000OO0OoOoo0ooO0o000000` is abstract but its constructor and four getters directly retain/return type, title, description and value strings. There are no local null checks, expression parses or normalization.
- CheckboxForms `oOOoOO0ooOoOoo0oOoOo000o` only forwards the literal type `checkbox` and its three strings to the parent constructor.
- RangeForms `oOooooooo00OO0OOO0oO00o0` forwards `range`, retains step/min/max doubles, and returns them directly. It has no local finite/positive-step or min<=max validation. Actual input validity may be constrained elsewhere; malformed values were not supplied to a widget.
- RadioForms `oO0oOOoO0ooo0O0OO0oo0oo0` forwards `radio` and retains/returns the supplied FifoHashMap reference. It neither copies labels nor validates their expression strings.
- ExtraAnimationButton `OOoOO0ooooOO00000oO0oOo0` retains id/name/sound and the ConfigForms array. Its getter returns that same array. Final fields do not make its array contents immutable.

The screen dispatches initial-form creation using instanceof CheckboxForms, RangeForms and RadioForms, not by parsing ConfigForms.type text. Those are three separate if blocks. A new unrelated ConfigForms subclass does not acquire a widget merely by returning a recognized type string. Native model construction and external subclasses are not closed by this finding.

## Radio selection preserves its actual boundary

The screen converts the initial result with transformNumber then Math.round. It resets selection to0 when negative or labels.size < selectedIndex. Equality with size is not reset by this predicate. It subsequently iterates actual label indices and tests equality for selected state; that selected index is not used as an unchecked direct array lookup in this path. Do not report an out-of-bounds crash from the comparison alone. Label names and expression values use the corresponding ordered FifoHashMap lists; refer to [asset helpers](MODEL-ASSET-HELPERS-RECOVERY-2026-10-17.md) for list/map ownership.

## Navigation cache is shared state, not a per-screen immutable snapshot

AnimationRouletteScreen retains model, animatable entity and supplied/model property maps by reference. Its static CACHE stores category/page pairs. The model-ID constructor clears CACHE when the string differs from the shared MODEL_ID, then updates MODEL_ID; if empty it adds a root/page0 pair. A present cached category selects its map. Missing category resets to the root map while preserving the prior page before init's ordinary range adjustment.

The nested constructor accepts maps and does not perform the model-ID comparison. It reuses the current cached category if present, otherwise resets to a root entry using the old page (or0 if no prior pair). The screen's current pair comes from that shared cache. This establishes mutable shared ownership, not a demonstrated cross-entity rendering error.

clickClassify tests CACHE.size >5 before adding the next category; size5 is allowed to grow to6. Preserve the exact list-size condition rather than rewrite the source comment as a universal five-level limit. It adds only when the category map lookup is nonnull. clickReturn removes the last entry and creates a nested screen when size>1; otherwise it requests screen close. addRootClassify clears the list then adds root/page0 and the requested category/page0 without validating category existence in that method.

clickConfig selects the button object from buttonMap, resets both scroll counters and calls init. init clears widgets; rebuilding value-dependent controls still uses the deferred expression/callback stages documented in [roulette UI](ROULETTE-EXPRESSION-UI-RECOVERY-2026-10-17.md). No screen-generation token or cancellation guarantee is inferred from widget clearing.

## Playing an animation uses a different fallback from expression forms

clickDefault first checks remote-channel presence. With a channel, it uses the last nonblank cached category (otherwise empty) and sends SetPlayAnimation directly through CHANNEL. For an associated Player it uses the two-argument constructor whose entity ID is−1; for another entity it includes that entity's ID. It does not always send the associated Player's explicit ID.

Without a channel and with a current LocalPlayer, it invokes that local player's capability playExtraAnimation(selectKey), even though the screen also holds an animatableEntity reference. This is a concrete local-fallback target distinction, not proof of an incorrectly opened maid screen. Optional chat feedback is gated separately; screen close occurs on the normal tail after these branches. None of those requests proves successful playback, server acceptance or visual output.

The expression-form path, by contrast, enqueues on the associated animatable entity before its optional relay. Keep animation selection, expression evaluation and roaming-value replication distinct; [transport route guide](EXPRESSION-STATE-TRANSPORT-INDEX-2026-10-17.md) connects the latter two.

## Reuse limits

Validate application-owned form inputs at a defined boundary, state whether arrays/maps are shared, and choose whether navigation cache is model-wide, entity-wide or per screen. These are explicit design choices for reuse, not patches applied to the target. Forge widget internals, native construction, actual callback scheduling and external event handlers remain separate evidence requirements.

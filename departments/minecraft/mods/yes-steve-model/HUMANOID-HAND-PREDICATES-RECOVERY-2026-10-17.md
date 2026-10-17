# Humanoid hold, swing and use controller predicates

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-seven declarations in seven owners: MainhandPredicate, OffhandPredicate, SwingPredicate, UsePredicate, ModelFormatVersion, HumanoidStateTracker and ConditionalHold. No independent semantic review, central promotion or target execution.

## Hold controllers are hand-specific

Mainhand `oOO0000O0oO0o0OooOOO0oO0` and Offhand `OoOO00O00O0o0OooOoO0O0oo` return STOP for null entity or preview. They return PAUSE when that particular hand is swinging, or the entity is using that particular hand. Unlike [ctrl.swing/ctrl.use](CONTROL-EQUIPMENT-PREDICATES-RECOVERY-2026-10-17.md), these checks actually compare swingingArm/getUsedItemHand with the requested hand. The checks themselves do not test sleeping.

Mainhand precedence after the gate and format lookup: TACZ hold adapter → SWarfare hold adapter → charged vanilla crossbow → player-or-maid fishing → item-change detection → ConditionalHold → STOP. Any non-null adapter PlayState is returned. Offhand has charged crossbow → item-change detection → ConditionalHold → STOP, without the mainhand gun/fishing branches. Special early returns occur before tracker update.

Item-change comparison reads the previous tracked stack. If that previous stack is damaged, use ItemStack.isSameItem; otherwise use ItemStack.matches. On mismatch store current stack then indicateReload. HumanoidStateTracker `oo00oOO00o0OOo0oO0OOOO00` stores the same ItemStack reference (putfield9/17), not a copy; therefore this is not a detached immutable snapshot. External ItemStack comparison internals and in-place changes are not executed here. Keep the previous-stack branch and reference semantics when adapting this logic.

## Conditional hold names

`oo00OoO0Oo0OO0oOoOoOoOo0` registers names separately for main/offhand prefixes (length14/13), accepting valid IDs/tags and extra categories. Tag tests remain an ordered ReferenceArrayList; ID/extra lookup uses sets. Extra `none` is excluded; known UseAnim values and full inner-category names are stored separately.

At evaluation, empty hand directly selects hold_mainhand:empty or hold_offhand:empty. Otherwise precedence is registered exact item ID → first registered matching tag → inner classifier category → allowed UseAnim lowercase(Locale.US) → empty string. Empty-hand selection does not itself check whether a matching animation clip exists. The classifier is documented in the [control equipment dossier](CONTROL-EQUIPMENT-PREDICATES-RECOVERY-2026-10-17.md). ConditionalHold is not the same interface as the direct ctrl prefix matcher: it first builds accepted tests from model names.

## Swing and use differ at idle

Swing `OOooo0o00o0Oo0O0ooO0OoO0` first rejects null/preview, then permits an IronsSpellBooks adapter override. A non-sleeping SlashBlade mainhand path is evaluated even without ordinary swinging. It indicatesReload when the coded animation is finished; a nonblank SlashBlade name with a present clip plays it, while a nonblank name with missing clip returns CONTINUE without assigning a new animation here.

Ordinary swinging requires not sleeping. swingTime==0 and successful addition of the SWING tick-state flag triggers indicateReload. It chooses conditional main/offhand swing using the actual swingingArm; a nonblank result plays once, else defaults to swing_hand or swing_offhand. When not swinging, it returns CONTINUE, not STOP. Existing coded-controller behavior determines how an already selected animation progresses.

Use `oOooO00OOoOoOOoo0OoOOOOO` rejects null/preview, then requires using item and not sleeping. ticksUsingItem==1 plus successful USING_ITEM flag addition triggers reload. Choose condition by actual used hand, otherwise use_mainhand/use_offhand; request LOOP. When not using, return STOP. The inherited tick-state set and clear lifetime is in [state tracker input](STATE-TRACKER-INPUT-RECOVERY-2026-10-17.md); these gates are not an unconditional reload every rendered frame. ConditionalSwing/ConditionalUse implementations are outside this cohort.

## Model-format playback policy

ModelFormatVersion `oOO0o0o00o00Oo00oO00OooO` returns true immediately for format >=19, meaning the [playCompatAnimation helper](PLAYER-MAIN-SELECTION-RECOVERY-2026-10-17.md) omits the coded loop override. For earlier format: missing clip returns false, otherwise use the clip's isCopiedFromDefaultModel flag. This is loop-selection compatibility, not decoding or model access authorization. It explains why an apparent LOOP/PLAY_ONCE argument at a hand predicate call is not always the effective clip loop type.

## Reuse limits

Preserve PAUSE/STOP/CONTINUE distinctions, adapter early-return order, actual hand checks, conditional-name precedence, stack reference retention and version-aware loop dispatch. None of these static branches proves visible animation success. Raw equipment/provider state, model clips, optional APIs and actual render output remain separate evidence boundaries. Scoped audit verifies snapshots and negative integrity controls only.

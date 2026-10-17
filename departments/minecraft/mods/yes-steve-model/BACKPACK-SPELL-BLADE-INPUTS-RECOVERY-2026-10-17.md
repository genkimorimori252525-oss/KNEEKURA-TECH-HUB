# Backpack, spell and blade animation inputs

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Sixty-three declarations across ten Java adapter/binding classes. No mapping promotion, independent semantic review or target/provider execution. In particular, the legacy Unsafe field access was only inspected statically, never invoked.

## Sophisticated Backpacks

Wrapper `oOOOOOooO00Ooo000OOo00oo` requires enabled client config and loaded mod version >=3.24.25; older version records incompatible warning. Disabled config returns without explicitly clearing a previously true flag, so this is not a proved dynamic reconfiguration contract. Both binding branches provide livingEntityVar has_sophisticated_backpack, absent provider false.

Real binding `O0o0ooo0000OO0OOoooOoooO` tests getBackpackItemStack(entity)!=null. Lookup first tries Curios when Curios is installed, returning any non-null result; only then, for Player, asks PlayerInventoryProvider for a rendered backpack and rejects an empty stack. Lookup itself does not re-check Sophisticated INSTALLED. Its normal call placement is gated by binding/layer setup; do not treat it as a standalone optional-dependency-safe method.

BackpackCuriosCompat `O0O0o0OooO0O00oOo000oOOO` selects exact back slot and delegates to existing Curios handler search for BackpackItem. Thus cosmetic/render-toggle semantics follow [Curios evidence](CURIOS-QUERY-EXTENSION-RECOVERY-2026-10-17.md). This is rendered-equipment provenance, not a search of every inventory slot or proof a backpack layer drew.

## Iron's Spellbooks

Wrapper `O0OoO0O0oOOOoOoOO0o0o0OO` uses loaded irons_spellbooks flag. Both branches register clientPlayerVar iss_animation; absent provider empty String. Inner `O0oOOOOoO00o0ooo0OOOo0o0` requires AbstractClientPlayer, retrieves PlayerAnimationAccess associated data under SpellAnimations.ANIMATION_RESOURCE, casts to ModifierLayer, and requires active layer with KeyframeAnimationPlayer. It returns String-valued extraData name or empty; a wrong layer object's cast is not locally guarded.

When called with an AnimationEvent, keyframe tick==0 triggers coded-controller indicateReload before name extraction. The query calls with event=null, so reading iss_animation does not itself perform that reset. Playback prefixes iss:, checks model clip exists, and uses ordinary no-loop-override playback. Blank input returns null; missing prefixed clip logs its name as error then returns null, allowing the outer swing predicate's other paths. No throttling is visible in this method; actual log frequency was not measured.

## SlashBlade routing and time

Wrapper `oOOoOOOo00OOO00OoOOoo000` marks loaded when slashblade container exists. Versions inside Maven range (,0.1.2] select legacy path; outside select resharped. Legacy init calls the old-field-offset helper. Both binding branches register livingEntityVar slashblade_animation; absent provider empty.

Animation helper `oo0oOOO00OOo00o0ooo00o00` recognizes ItemSlashBlade OR YSM slash-blade item tag, gated by loaded wrapper. It reads mainhand blade capability and computes `(entity.level.gameTime - lastActionTime) * 50` as long, with no partial tick or local nonnegative clamp. Resharped path uses the capability interface; legacy requires SlashBladeState type, otherwise empty. Query and event entry points both use this combo-name route. Main movement override prefers a present slashblade:baseName clip, otherwise baseName, preserving explicit loop type.

Resharped helper `OO0Oo0oo0oO00Oo0O0o00o0O` resolves combo registry ID; absent combo gives empty. Timeout uses provider timeoutMS, minus553 for exact slashblade:standby. Names remain valid while time<=timeout. One alias maps slashblade:combo_a4_ex→slashblade:combo_a4ex. Off-ground judgement_cut and judgement_cut_slash_just2 select their respective judgement_cut_slash_air and judgement_cut_slash_air_just2 names. No broader alias normalization is implied.

Legacy helper `oo0OOOo0oo0oo00O0oooOo0O` initializes FIELD_OFFSET=-1 and attempts a field offset for comboSeq. Its NoSuchFieldException path does not establish a valid offset. Later getObject has no local offset-validity check; do not run this helper independently or claim that declaring the adapter proves legacy compatibility. If the returned object is old ComboState, time>timeout returns empty; otherwise remove leading ex_ if present and prepend slashblade:. Actual offset validity, external layout and version behavior remain untested.

## Reuse boundary

Keep loaded/version/config gates separate from successful provider initialization, query-only versus playback reset behavior, rendered backpack selection versus general inventory, and legacy versus resharped combo naming. These are visual adapter contracts, not model decryption or access-control work. Scoped audit checks fixed bytes/source/negative mutations; not an external compatibility or runtime test. Later than the fixed nine-cohort checkpoint.

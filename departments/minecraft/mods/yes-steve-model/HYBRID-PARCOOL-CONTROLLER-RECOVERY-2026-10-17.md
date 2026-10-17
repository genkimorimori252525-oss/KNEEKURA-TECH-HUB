# Hybrid controller and ParCool selection join

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty-four declarations in six owners: ParCoolCompat, ParCoolCtrlBinding, ParCoolAnimationManger plus synthetic enum switch holder, ParCoolPredicate, HybridAnimationController. The misspelled source name Manger is retained. No central promotion, independent semantic review or target runtime. Actual JDK javap was also used to inspect Hybrid, manager and predicate; this executes the disassembler, not target classes.

## General hybrid controller, not a ParCool-only mechanism

Owner `oO00oooOoOo0O0oOo000o0Oo` constructs both coded and Bedrock controllers and initially points activeController to coded. updateModel looks up controller data by the controller's name:

- Data present: set isBedrock, update Bedrock then coded model inputs, active=Bedrock.
- Data absent: unset isBedrock, update coded, clear Bedrock, active=coded.

process in Bedrock mode always processes Bedrock first (offset14), then checks its builtin-state flag. If builtin, enter coded mode only when active was not coded: clone/start the state's blend transition (52), assign it to coded (57), switch active (65), then process coded (75). Subsequent builtin frames do not restart that transition merely because process is called again. If leaving builtin mode while active was coded, finalize coded animation context (97), reset coded (104), then switch active to Bedrock (112). This sequence has no local finally/rollback. Without Bedrock mode, process only coded (125). The same allowEmitting value is passed through.

Bone queue visitation and blendRotation delegate only to activeController. They do not combine both controllers' queues. State-name text uses `[builtin] ` plus coded name when Bedrock is in builtin state; otherwise names the relevant state. clear clears both controllers in Bedrock mode, otherwise coded only, and does not itself reset isBedrock/active pointer in this body. See existing [Bedrock](BEDROCK-CONTROLLER-RECOVERY-2026-10-17.md) and [coded](CODED-CONTROLLER-STATE-RECOVERY-2026-10-17.md) dossiers for internal state details.

## ParCool availability and entry

Compat owner `oo0oO00OO0oo000oOOOOoO0o` honors ENABLE_PARCOOL_COMPAT when non-null; false explicitly disables and returns. Loaded mod first-entry version must compare >=3.4.1; lower version records incompatible. No provider means default-disabled. This is the captured startup path, not dynamic hot-unload support. Enabled animationPredicate returns a factory creating the general hybrid controller with 0.1f transition parameter and ParCoolPredicate. It does not force every frame to use coded animation when model-supplied Bedrock controller data exists.

The ctrl.parcool_state adapter (`ooO0000o0OO0O000OOooOOo0`) returns empty string without provider/non-player. With a player and non-null selected name it strips the first seven characters (`parcool:` length) without independently validating that prefix. It does not locally handle a shorter non-null string. Normal special/fallback names are prefixed, but blank class names can produce empty string in the naming helper; do not claim this was observed at runtime.

## External animator → local name

Manager `o000oo00OO0Oo00ooOOoOO0O` asks external Animation.get, requires hasAnimator, obtains animator through a mixin accessor, then requires Parkourability. CrawlAnimator is explicitly excluded so base crawling can remain available. Animator.shouldRemoved also returns null. No provider or mixin execution was performed.

Special dispatch has directional names for cliff clinging, dodge, flipping, horizontal wall run, hang, roll, speed vault, wall jump and wall slide. Captured synthetic enum switch arrays preserve exact enum-constant mapping, not assumed ordinal stability. Wall-slide absent direction chooses right; otherwise body-yaw-relative normalized direction chooses right for z<0, left otherwise. External accessor injection, action objects and provider vector implementation remain unverified.

Fallback names use a class-keyed HashMap.computeIfAbsent cache. Blank simple class name returns empty; trailing literal Animator is removed; each uppercase character after index0 receives an underscore before lowercase conversion; prepend `parcool:`. This is character-wise conversion, not a linguistic acronym splitter. Class identity is the cache key; it is not per-player action state.

## Important priority/model distinction

Manager.hasAnimation only checks that its selected name is nonblank. It does not check whether the model contains a matching animation. The [base CtrlBinding selector](CONTROL-PRIORITY-ACTIONS-RECOVERY-2026-10-17.md) uses this condition to suppress base locomotion selection. ParCoolPredicate (`oOoOOoOOoOooOoO0oO0OOoOO`) separately rejects null player/preview with null, gets the name, and checks actual model animation existence (offset50/53) before playAnimation (59); otherwise returns STOP (63).

Therefore a selected external animator name and an available model clip are different prerequisites. A missing clip can meet the base suppression condition while this coded predicate returns STOP. This is a conditional static integration concern, not proof of visible freezing: model Bedrock logic, other controller layers, caches and runtime scheduling can alter the outcome. Do not silently add a guessed fallback or patch upstream behavior.

## Validation boundary

Scoped audit compares exact methods, declarations, switch operands, exception tables, bootstrap/constants and pinned source files; missing-body controls are rejected. Captured support is not exhaustive external compatibility proof. Native renderer and actual ParCool/Minecraft behavior remain unexecuted.

# Fixed-artifact animatable override and direct async caller closure

Primary static inventory; independent review NOT_RUN. Exact artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` only.
No new mapping promotion or runtime execution. This report uses exact JVM names
and descriptors already grounded by the preceding dossiers, not a source search
as proof that the distributed artifact has no additional overrides.

## Closed inventory, bounded interpretation

Scanning all955 classes finds12 classes in the superclass chain rooted at
`o0000OoOooO0oo0o0oooo0Oo`, including the root. The inventory retains each owner's
superclass and all declarations for the two exact target method signatures.

For canUpdateAsync's exact `OO0O00oO0OOO00oOO0OoO0OO()Z` signature, only
CustomEntity `oOo00OoOO00O000ooO0Oo00o` declares it; its body returns true. There
is no override of that exact method among the inspected descendants in this JAR.
This is not proof every instance is scheduled: constructor registration, model
readiness/configuration and world/activity gates still control eligibility. It
also does not cover classes added by other mods or runtime transformers.

For isImmutableRender's exact event-to-boolean signature, five owners declare:

- Base AnimatableEntity returns true.
- CustomEntity returns event level-exclusive OR Iris shadow result.
- CustomPlayerEntity `oo0OooOO0oOoOoOoo00oO000` returns event level-exclusive OR
  (not localPlayer AND Iris shadow result). The local-player field gate at11
  precedes the external shadow query at14; local-player shadows alone do not
  qualify this branch as immutable.
- `O00000oOo0o0o00OOoo0O0oo` returns true. Its no-arg constructor instantiates a
  nested player and invokes CustomPlayerEntity(Player,false,false), matching the
  prior official GUI-preview candidate structure; original class name not newly
  promoted here.
- `oo0000o0OO0OooOo00oO0O0o` returns true. Its constructor takes LocalPlayer plus
  a model capability and invokes CustomEntity(Entity,false), matching the
  first-person-arm candidate structure; not a new central class-name promotion.

The full declarations and instruction bodies are in ANIMATABLE-OVERRIDE-EVIDENCE.
The two candidate class descriptions are context from source/constructor evidence,
not independently reviewed symbol recovery. Constructor bodies are available in
the fixed artifact but are not part of this narrow override evidence file.

## Direct async call sites

The scan finds four matching direct invoke references: one beginAsyncUpdate call
from AnimationParallelTicker.scheduleAll, one waitForAsyncUpdate call from
AnimationParallelTicker.waitAll, and two wait calls in CustomEntity.updateAnimation.
This agrees with the bounded producer/consumer paths in ASYNC-ANIMATION-RECOVERY.

The matching rule is deliberately exact: begin uses the grounded CustomEntity
owner/name/(F)V signature; wait uses its grounded name/return descriptor with
owners in the scanned superclass family. This is not a generic whole-program
call graph: reflection, invokedynamic indirection, external classes and renamed
runtime transformations are not ruled out. One direct submit call site does not
prove exactly-once scheduling, because the site itself can execute repeatedly.

## Reproduction and next question

Run tools/animatable_override_ysm_265.py with --jar, --evidence and --out to
recompute the entire fixed-JAR inventory. Three structural checks pass and five
missing/corrupted-inventory controls reject. --capture writes fresh evidence;
it is not verification and must not be substituted for the comparison pass.

Next follow model-update/registration and renderer consumers to establish when
these overrides actually apply, and decode Mixin annotation targets if exact hook
placement is needed. Existing static reports do not establish runtime safety.

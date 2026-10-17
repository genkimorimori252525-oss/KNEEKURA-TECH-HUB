# Bedrock controller: state selection and queue-production join

Status: primary static analysis; independent semantic review NOT_RUN. No central
mapping promotion and no runtime execution. The 669-row mapping is unchanged.
Artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
source candidate revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
Whole-source equivalence remains NOT_ESTABLISHED; prior divergence is preserved.

## Bounded identities

Main owner `O00Oo0oo0Ooo0oOOOo0OO0oO` has 15 methods. Nested condition holder
`$O00OOOooOoooOoo0o0o0oO0O` has 4; player holder `$Oo0Oo0o00O00Oo0OOoOOoooo`
has 6; blend queue `$o0OOooo0o0OO00OoOOOo0o0O` has 11. All 36 declarations,
complete instruction/encoded operand streams, handlers and bootstrap records are
retained in BEDROCK-CONTROLLER-EVIDENCE. Source is the pinned official
`geckolib3/core/controller/BedrockAnimationController.java`. Candidate names below
are semantic labels, not proof of original obfuscated symbols.

## State selection happens before condition refresh

`process(event,evaluator,allowEmitting)` calls updateState at offset 55, then
condition evaluation at 305 and player process at 336. updateState reads the
condition holder's stored boolean at 112; it does not reevaluate that expression.
The holder constructor sets result true. Setting a nonnull condition retains the
previous result; setting null sets true. Thus completion predicates use stored
condition results before this call's refresh. This is ordering, not a proven bug.

updateState initializes anyFinished=false/allFinished=true; applied players can
set any true or all false. If none apply, any becomes true (165), leaving all true.
Transition predicates are visited in list order. A false predicate continues;
a true predicate with missing destination or a destination already in skipPathSet
returns false at 268–269 rather than trying later transitions. process clears the
set once per call and repeats successful state changes while active player count
is zero. This bounds visited-state cycles on the ordinary path, not arbitrary
expression execution time or external mutation.

## False conditions suppress emission and blended output, not player processing

The allowEmitting/shouldApply AND is constructed at 317–335. Both paths converge
on player process at 336 with the boolean argument. All active player holders are
processed in this loop even if their condition is false. Dirty aggregation later
adds each active player's bone queues together with its condition holder; it does
not filter players out at insertion. Queue visitation tests the blend queue's
shouldApply at 63 before consumer.accept at 71. Existing blend-queue poll evidence
then filters individual pairs by condition. This distinction joins the prior
player-clock finding: emission permission is not a general timeline pause gate.

## Transition initialization and homogeneity limitation

transition first stops sounds, enables emission at 31–32, recursively exits an
old child where present, evaluates old onExit, then new onEntry/sound entries.
It disables emission at 244–245 on the normal path, stores state at 250,
deactivates/clears active blend queues, then marks aggregation dirty at 297–298.
There is no exception-handler/finally coverage in this method.

Null, builtin and sub-entry states use zero players; others use animations.size.
Surplus players are finalized/reset. Each selected holder updates its model if
dirty, receives its condition, finalizes context, receives
newState.blendTransition().startNew() (523–531), is marked reload, and selects its
animation (555). All these players are subsequently processed with the same
renderTicks in this process call. This supports synchronized initialization on
this path, but does NOT prove all future points share a beginning subtype or
transition duration: per-player startNew results, missing animation selection,
loop/ending states and external implementations remain dependencies. The source
comment assuming homogeneous beginning transitions is not a proof that the
previously documented unchecked blend cast is universally safe.

## Hierarchy and side-effect boundaries

- Main process compares depth with exactly 5 (`iconst_5`, `if_icmpeq`, 95–96),
  not a greater-than-or-equal range guard. Root constructor uses 1 and normal
  child creation increments depth by 1, so this path stops delegation at 5.
- On an updated sub-entry, a missing subData does not clear an existing child.
  Record as conditional retention, not proof that ordinary input triggers it.
- Queue visitation contains exactly one child delegation at offset 29; it does
  not double-visit the child. Main process child path returns before its own loop.
- Sound entry dispatch calls external StringUtils.isNoneBlank at 198 and skips
  playSound when its result is true (201→232). This captures actual polarity;
  external dependency implementation and audible runtime outcome are not tested.
- clear empties data/state/queues/players and stops sounds; only root depth 1
  clears the child reference. Model/data ownership and scheduler reentry still
  need the animatable lifecycle cohort.

## Verification and next seam

`tools/bedrock_controller_ysm_265.py` checks all 36 methods against the fixed JAR,
all four owner declarations/bootstrap records and pinned source bytes/revision.
200 checks pass; 20 corrupt/missing-evidence controls are rejected, including
condition caching, transition priority, hierarchy comparison and invented finally.
These are static snapshot integrity checks, not executable JVM behavioral tests or
independent approval of this prose. See the companion verification JSON.

Next: animatable model reload/update scheduling and the call boundary supplying
renderTicks/shouldTick, then revisit the remaining homogeneity prerequisites.

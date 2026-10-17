# Control priority and coded-controller action queries

PRIMARY_STATIC_REVIEW_ONLY; exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No central mapping promotion, independent semantic review or target execution. Captures 47 declarations across CtrlBinding, its two nested types and four action functions. Abstract predicate declaration has no invented Code. Supporting constructors/lambdas/record methods are not counted as new recovered behaviors.

## Main-animation selection

Exact owner `OoOOOOOo0oo0000oooOOOoOO` registers nineteen base names in priority groups, in the following insertion order:

- 0: death, riptide, sleep, swim, climb, climbing, ladder_up, ladder_stillness, ladder_down
- 1: fly, elytra_fly
- 2: swim_stand, attacked, jump, sneak, sneaking
- 3: run, walk
- 4: idle

Registration allocates five condition lists on first use, appends the condition, and registers a living-entity variable that asks the common selector about its own name. This is a first-match priority selection, not nineteen independent booleans. The common `(String,IContext)Z` method:

1. Reads the animatable's state tracker. Any non-null cached string (including empty) returns name equality immediately, before further guards.
2. On an uncached result, preview animatable, player with ParCool animation, or non-null vehicle that is alive suppresses base selection by writing empty string and returning false. The vehicle test is `isAlive`, not a player-only riding gate.
3. Iterates priority 0 through 4, each list in insertion order. First true predicate writes its name then returns whether it is the queried name. Exhaustion writes empty string and false.

Binary anchors: cache branch24/equality32; preview45; ParCool call72; vehicle alive104; priority bound125; predicate167; selected-cache write181; no-match write207. Cache reset lifetime is in the existing [state tracker cohort](STATE-TRACKER-INPUT-RECOVERY-2026-10-17.md); do not infer a fresh decision on every query call. Child contexts can share an animatable while replacing entity, so this method's cache is not automatically keyed by child entity.

Movement predicate uses Minecraft partialTick to sample walkAnimation speed, absolute value strictly greater than 0.05. It is not a world-distance velocity check. Ladder sign uses `20 * float(position.y - yo)` and exact zero for stillness. Flying prioritizes nonlocal PlayerAnimatableCapability tracker state; otherwise Player abilities flying, otherwise false. The extra-animation variable additionally requires CustomPlayerEntity, playing-extra flag and CAP controller state not IDLE.

The constructor calls ten optional-mod registration adapters. Capturing those call sites does not establish every optional predicate's semantics or provider availability. Base name groups above are not a complete runtime compatibility catalog.

## Action functions

All four extend ContextFunction<Object> and obtain `animationEvent().getCodedController()` first. A missing coded controller returns null before argument evaluation. There is no allowEmitting check in these action bodies; do not copy the particle/sync emission gate onto them. The call chain does not locally guard a null animationEvent.

- `set_animation`: owner `o0Oo0oO0OO00O0ooOo0o0Ooo`, arity one or two. Empty/null string aborts. One argument uses null loop override. Second integer maps 10→LOOP, 11→PLAY_ONCE, 12→HOLD_ON_LAST_FRAME; any other value also uses null. Exact tableswitch offset62; setAnimation call114. Whitespace is not trimmed here. Return null is not a play-success receipt.
- `set_beginning_transition_length`: `OOo00o0o0oo0oOOOoOOOoooO`, arity one. Float argument; negative rejected, zero permitted, no upper bound in this body. Compare35/branch36, controller setter44. Argument conversion behavior is documented separately; do not infer validation of all non-finite inputs from this single comparison.
- `reset`: `ooOoo0OooooOOOO0oOoO0OOo`, arity zero, calls coded-controller reset then null.
- `indicate_reload`: `O0o00oo0Oo0O0oo0oOOOOOOO`, arity zero, calls distinct indicateReload then null. It is not evidence that assets were reloaded successfully.

Constants registered by CtrlBinding are state_continue=2, state_stop=3, state_pause=4, state_bypass=5; loop=10, play_once=11, hold_on_last_frame=12. ContextBinding's constant-value wrapper is covered by [typed guards](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md). Controller-side handling remains in [coded-controller state](CODED-CONTROLLER-STATE-RECOVERY-2026-10-17.md); action entry points do not prove native render results.

## Verification

Run only the scoped `tools/control_priority_actions_ysm_265.py` when changing this evidence. It verifies fixed bytes/declarations/operands/source anchors and rejects missing evidence mutations. Integrity success does not independently prove the prose semantics or run a Minecraft instance.

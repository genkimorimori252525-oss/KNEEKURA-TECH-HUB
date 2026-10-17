# Coded/predicate controller state decisions — 2026-10-17

Status: primary static review; independent semantic review pending. No new central
mapping rows. This deepens already-known method shapes rather than counting them
again. Exact owner `oo000oooo0OOoo00O0o0OOOO` retains its existing historical
PredicateBasedController label and source-divergence flag. The official candidate
counterpart is CodedAnimationController; the older map is not silently renamed.

The artifact is fixed to Zqooxsd2 SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
The complete controller and two enum snapshots retain 30 methods, declarations,
constant/bootstrap data, all operands/handlers, and four official source hashes
at `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.

## Decision order and context lifetime

process first sets this controller on the AnimationEvent, then evaluates the
optional Molang predicate. Only a null result invokes the Java animation predicate.
The event's controller reference is cleared afterward at offset32. There is no
exception handler: a predicate exception can bypass that clear and subsequent
state publication. Caller recovery/event reuse is not established by this fact.

The Molang helper returns null immediately when no predicate exists. Otherwise it
updates its controller-context finished flags, installs controller and animation
contexts, and sets allowEmitting **true** before evalAsInt. This setter request is
independent of process's incoming allowEmitting argument; it is not proof that any
particular effect is actually emitted by callees.

After a normal evalAsInt return it sets emission false and both contexts null.
These are ordinary sequential calls, not finally restoration, and no prior values
are saved. The switch interprets integer **2→CONTINUE, 3→STOP, 4→PAUSE**, default null.
Those values are grounded in exact tableswitch operands and enum initializer names,
not enum ordinals or guesses from source symbol names. A default null then permits
the Java predicate fallback in process.

## CONTINUE, STOP and PAUSE are distinct instruction paths

- CONTINUE calls the player process with incoming ticks/evaluator/emission flag,
  then sets the controller pause flag false.
- STOP reads the player state once. If that captured state is BEGINNING_TRANSITION
  or RUNNING, it calls stop then indicateReload. The following test for
  ENDING_TRANSITION uses the **same captured state**, not a refreshed getter.
  Therefore changing state inside stop does not cause that later branch to become
  true in this invocation. If the captured state was already ENDING_TRANSITION,
  player process is called. Pause is then set false.
- PAUSE still calls player process, explicitly passing emission false. It then calls
  resetBoneAnimationQueues and sets pause true. Thus the controller does not simply
  skip all player work on PAUSE. Whether playback time advances/freeze compensation
  occurs is a question for the player, not settled by this call alone.
- A null result from the Java predicate matches none of the three identity branches;
  no local action resets the previous pause flag. Normal tail publication still
  queries the current player state and sends it to the animatable entity.

No branch has a local catch or rollback. Calls may prevent later updates if they
throw; these are control-flow limits, not reproduced defects.

## Pose enumeration and legacy blending

visitBoneAnimationQueues checks pause first and emits no queue wrappers when it is
true. Otherwise it iterates the player's active queues and creates a new single-
queue wrapper per visit. Combined with the PAUSE branch above, 'player process was
called' does not imply those queues will be exposed to the processor afterward.

blendRotation returns true only when both the configured legacy blend flag and
player state RUNNING hold. The source comment describing this as a temporary fix
is author context; no historical fix effectiveness is measured here.

## Model handler selection and reset delegation

updateModel first updates the player model and its beginning transition, then clears
the stored Molang predicate. It replaces every dot in the controller name with
`_ctrl_`, looks up that handler list, and selects only element zero if nonnull and
nonempty. It does not evaluate or combine all handlers.

reset delegates to player.reset; clear delegates to player.clear and nulls the
Molang predicate. Neither method explicitly writes the controller pause field.
Do not describe them as a complete local-state reset without reviewing the next
process/visit ordering. finalizeAnimationContext delegates to the player; no
callee cleanup guarantee is inferred from the name.

## Verification and next boundary

170 strict checks and 16 corruption controls passed. The tool enforces full
30-method closure, three exact declarations/bootstrap tables, four fixed source
records and checked source files/revision. Controls mutate fallback, event clear,
pause emission/flag/visitor, STOP gate, predicate emission cleanup, switch bytes,
enum names, invented handlers and omitted evidence. Target Java/JNI/game execution
was not performed; independent review is pending.

```bash
python tools/coded_controller_state_ysm_265.py --jar /absolute/path/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence CODED-CONTROLLER-STATE-EVIDENCE-2026-10-17.json \
  --out /tmp/ysm-coded-controller-audit.json
```

Continue into AnimationPlayer state/tick/transition production, then the Bedrock
controller's active-queue aggregation and Java scheduling/wait boundaries. Keep
all higher-caller and runtime claims separate. This is not whole-target completion.

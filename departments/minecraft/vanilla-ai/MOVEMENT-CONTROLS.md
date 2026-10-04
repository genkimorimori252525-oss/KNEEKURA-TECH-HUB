# Movement controls — Minecraft 1.20.1 ANCHOR

Evidence: base/flying/swimming MoveControl, LookControl, JumpControl, BodyRotationControl, Ghast/Phantom/Slime nested classes and representative constructors in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

The base MoveControl exposes operation-associated wanted coordinates and speed modifier. `hasWanted()` is a statement about the base controller's operation, not universal proof that a custom Mob lacks a desired move target. The observer must identify the actual controller class and declare which fields its adapter understands.

FlyingMoveControl changes vertical/yaw handling and gravity behavior within its own tick. SmoothSwimmingMoveControl has swimming-specific pitch/yaw/acceleration logic. A viewer must not convert these into a conventional ground path merely because Mob inherits PathNavigation.

LookControl exposes whether it is looking at a target and cached wanted coordinates. Its look operation is separate from MoveControl and navigation. JumpControl has a private desired-jump flag in the captured class; a public tick is an actuator, not a read API. BodyRotationControl is another execution component.

## Custom families

| Family | Proven static mechanism | Observation limitation |
| --- | --- | --- |
| Ghast | RandomFloatAroundGoal / GhastMoveControl / custom reach test; shooting Goal | No fabricated A* path; reach-test candidates need original-invocation capture |
| Phantom | Attack strategy/circle/sweep Goals, PhantomMoveControl and PhantomLookControl | Its private moveTargetPoint/phase are distinct from base wanted coordinates |
| Slime | SlimeMoveControl with direction/jump delay plus specialized Goals | Do not equate every hop with a selected conventional path |
| Dolphin | WaterBoundPathNavigation, SmoothSwimmingMoveControl and SmoothSwimmingLookControl | Swimming evaluation/control cannot use ground-field semantics |
| Enderman | Conventional goals plus teleport paths in entity code | Teleport is a trace break, not an observed line through intervening space |

These are class/member/method-body findings for the captured development generation. Actual native targets, phases, reach tests, steering and motion must be retained separately before runtime acceptance.

## Hook policy

Public getter snapshots may report bounded base fields with explicit `BASE_CONTROL_FIELDS_ONLY` semantics. A custom controller adapter exposes additional fields only after exact owner/member verification. Missing private/custom fields remain `NOT_EXPOSED`; a zero/default base field must not be substituted for them.

Never tick a Move/Look/Jump/Body control to inspect it. Never alter controller operation, wanted coordinates, speed, random stream or navigation to create a visualization. Diagnostic instrumentation overhead is measured rather than assumed absent.

## Original Ghast reach callback continuation

The pinned `Ghast$GhastMoveControl` class SHA256 is `9cf70e9f2224e83c26b76de3ed734789c44e6e61d016550e443bea8b1de8934d`; normalized disassembly SHA256 is `5602ddf2ea35d4692483668446b2d2b235611b8b3437dfa198f406a86893ec3d`. Original `tick` at bytecode offset109 invokes its private `canReach(Vec3,int):boolean` with normalized wanted-position displacement and `ceil(distance)`. The control's countdown delays such tests; not every tick evaluates a candidate.

`canReach` advances the current bounding box by the passed direction for steps1 through length-1 and returns false at the first failed original `Level.noCollision` call. Length0/1 returns true without a loop collision query. A true result is this algorithm's returned feasibility value, not proof of every point/destination being collision-free, arrival, successful attack or globally chosen path. False does not expose the actual blocked cell, first failed step or high-level reason.

One non-cancelling RETURN Mixin now captures this original boolean and passed direction/step count under the existing explicitly armed `control` burst. Exact selected Ghast/controller reference, cached UUID, SERVER thread and unchanged context/window/event/byte bounds apply. No extra reach/collision/controller/random invocation is performed. `CONTROL_GHAST_REACH_RETURN` becomes direct EVALUATION with partial `custom_flight_reach`; CANDIDATE/SELECTION/reason/collision location remain unknown. Direction arguments are not additional Motion positions or A* nodes.

Three retained regressions establish true/false, strict malformed-data refusal and late-arm/other-identity absence without reconstruction. Genuine mapped producer tests and Gson→Node interop establish the source contract and suppression fences. [Frozen native-r40](GHAST-ORIGINAL-REACH-ACCEPTANCE-2026-10-04.md) subsequently captures112 actual returns (109true/3false),287 real Mob position samples and separately identified projectile facts; post-budget packet intervals remain NOT_CAPTURED. This is bounded runtime proof, not complete candidate/collision/cause, custom-MOD or paired observer acceptance.

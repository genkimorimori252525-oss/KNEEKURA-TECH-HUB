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

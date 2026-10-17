# Vehicle/projectile controllers and root-rotation adapter

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eighty-one declarations across twelve owners: two controller collections/adapters, four predicates, vehicle-origin controller/queue and two aircraft adapters. No mapping promotion, independent semantic review, target runtime or aircraft simulation.

## Collections and resource presence

Projectile collection `oOooOoO0O00OOOOooOoooOOo`: pre_main → main → post_main → parallel. Main uses the projectile predicate ANIM_LIST for SingleControllerDiscovery; pre/post use null animation lists. Vehicle collection `OOO0o0oO0o0OO0O00OOO0ooo`: pre_parallel → pre_main → main → move → origin → ride → post_main → parallel. Origin is an unconditional simple factory; other main/move/ride entries use SingleControllerDiscovery with named animation lists. Both use lazy static collection initialization and model-specific animation/controller adapters with no armor conditions.

Both collections pass multi=false to ParallelControllerDiscovery, restricting controller/event suffixes to one digit0–7. This differs from player/first-person collections' multi=true. Final parallel uses the legacy blendRotation=true constructor; vehicle pre_parallel uses ordinary constructor. Resource presence admits a factory; hybrid model logic can then choose Bedrock rather than the coded predicate. See [discovery semantics](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md) and [hybrid switching](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md).

## Coded state names

- Vehicle main `o0OO00OO000o0OOOoO00O000`: null entity STOP; water before onGround, otherwise fly. These are animation states, not control of flight physics.
- Vehicle move `OoOOO0OOoOo0OOOO0oO0O0oO`: null STOP; sqrt(delta.x²+delta.z²)>0.05 selects forward, else idle. No vertical component, yaw-relative projection or multiplication by20. Negative/reverse horizontal motion still contributes positive speed.
- Vehicle ride `OOO0o0o0OOO000oOOOooOOo0`: null STOP; any nonempty passengers list selects has_ride, otherwise not_ride. Unlike humanoid passenger predicates, no first-passenger alive test here.
- Projectile main `o0o0Oooo0ooOO00ooooOO00o`: null STOP; water before fire before IArrowExtraInfo.isInGround; remaining case selects literal air. Ground is the arrow interface flag, not general entity.onGround.

Important literal mismatch: projectile static ANIM_LIST is water, ground, fly, fire (fly at clinit16), but its final coded setter uses air (predicate81). The collection passes that list into discovery. Thus a model with only air and no qualifying controller/event/other listed clip does not qualify through this animation-list gate; a model qualifying via fly can still have the coded airborne branch request air. This is a static naming-contract discrepancy, not a reproduced rendering failure; preserve both literals rather than silently correcting upstream behavior. Model Bedrock logic may bypass coded selection.

## Origin queue and retained rotation

VehicleOriginController `oo0Oo0O00oooOoOo0O0oOOOo` retains the first element of supplied top-level bone snapshots, not a bone selected by name. Empty list means no root. process asks ImmersiveAircraft rotation first; Optional.or lazily tries SimplePlanes only when absent. A present result becomes a new AnimationVec3 and requests ending-transition progress reset to0. allowEmitting is not read in this body.

An absent result does not clear the previous rotation field. Queue visitation requires both root and rotation; queue pollRotationPoint returns the retained value without removing it; position/scale return empty. clear explicitly nulls root and rotation. Therefore this is a retained rotation source, not an event queue whose poll consumes one sample. A stale-rotation concern requires the actual lifecycle/provider transition to establish a visible issue; no such runtime test was performed.

## Aircraft provider boundaries

Both adapter init methods check loaded mod presence inside a Throwable catch; no provider validation or execution is implied. ImmersiveAircraft adapter `oO00Oo00O000O0OoooO0oOo0` requires enabled flag and AircraftEntity, uses zero wind effect when grounded else provider getWindEffect, then composes X wind.z, Z wind.x, negative view pitch and negative roll rotations in the captured order before local EulerZYX extraction. The Euler helper is separate existing math evidence; external aircraft/JOML behavior was not executed.

SimplePlanes adapter `Oo0ooOOO0oO0oOO0oOOoo0o0` asks external lerpQ(partialTick, previousQ, clientQ), premultiplies negative view yaw, optionally applies Z hit wobble, extracts EulerZYX and negates result.x. Do not claim the returned quaternion is a fresh copy: that belongs to the external lerpQ implementation. The hit-wobble call preserves actual org.joml.Math.clamp argument order `(timeSinceHitWithPartial/10, -30, 30)`; it must not silently be reinterpreted as a guaranteed conventional value/min/max clamp. Exact loaded JOML behavior is a dependency boundary, as already distinguished in [player property/query evidence](PLAYER-PROPERTY-QUERY-RECOVERY-2026-10-17.md).

These are Java animation inputs and bone-queue production. They neither prove world-space aircraft orientation correctness nor mutate vehicle movement here. Native renderer output, external physics and actual model clip availability remain unverified. Scoped integrity audit checks exact declarations/operands/bootstrap/source and negative mutations; later than the fixed nine-cohort checkpoint.

# Goal / Brain method-body research — 2026-10-04

Status: **STATIC B2/B3 EXPLANATIONS EXPANDED; INTEGRATED NATIVE ACCEPTANCE REMAINS OPEN**.

This addresses the named Goal and Brain research in [original sections B2/B3](../LOCAL-EXECUTION-HANDOFF-2026-10-02.md). It adds explanations and proof locators, without changing gameplay, observer channels, Viewer behavior, dependencies or the original ledger. It does not close the full section 21 checklist.

## Evidence and reproducibility

The [additive ledger](GOAL-BRAIN-BYTECODE-LEDGER-2026-10-04.json) records 26 exact class identities, 204 selected method locators and 27 field locators. It shares these immutable identities with the original [61-class ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json) and [Foundation Map](../vanilla-foundation/LOCAL-GENERATION-2026-10-03.md):

| Item | Identity |
| --- | --- |
| Minecraft / Forge | 1.20.1 / 47.2.0, Mojmap resolved-userdev |
| Artifact SHA-256 | `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb` |
| Foundation Map | `522cbb565d187f8e1e7b97140206f5ac11e8ca90719528bd661f875f184e34fd` |
| IndexSnapshot | `55a63559b62697c11e8ece0cd2fcb97d2db4730684789a31240b2c515f08ba06` |

The local research rehashed the genuine artifact, JDK javap executable, JDK release/modules, original class bytes and old retained disassemblies. Additional owners were disassembled with the same recorded `-private -s -c -l -verbose` provider. Each selected method/field has a descriptor, private whole-disassembly line range and SHA-256 of its exact retained UTF-8 slice. That slice includes metadata and is not a canonical bytecode-only hash. Whole outputs, JAR/classes and machine paths remain private. The original ledger is unchanged. Locators establish retained proof material; they do not imply that every member or subclass was semantically explained.

## Original requirement mapping

| Required area | Concrete explanation / source members |
| --- | --- |
| Goal API and lifecycle | [Goal system](GOAL-SYSTEM.md): abstract canUse; continuation's virtual delegation; no-op base lifecycle; default interruptibility/every-tick flag; delay helper; mutable owned flags. |
| WrappedGoal | Delegation, priority comparison, guarded start/stop and field-before-callback ordering; original exceptions remain a separate outcome. |
| Selector / targetSelector | LinkedHashSet iteration, all-flags ownership, disabled checks, sentinel, cleanup → update → running ticks; independent selector identities. |
| Priority / replacement / cadence | Strictly lower numeric replacement plus owner's interruptibility; exact Mob reduced/full branch, target-first ordering and every-tick filter; unused newGoalRate body boundary. |
| Sensor / SensorType | [Brain system](BRAIN-SYSTEM.md): supplier/registration, constructor-created sensors and required keys, random initial phase, decrement/reset/scan distinction. |
| MemoryModuleType / MemoryStatus | Optional wrapped codec; registry key vs current value; unregistered/empty/present truth table; writes and empty-collection erasure. |
| Expiry / removal | Long.MAX_VALUE sentinel, expiry-before-decrement, retained registration, activity-configured erasure and explicit clear/erase methods. |
| Activity / Schedule | Registry/equality; score selection, tie-order uncertainty, Timeline step values/deduplication/cursor mutation, caller's >20 game-time gate. |
| Priority buckets / requirements / core/default/active | TreeMap → per-priority activity HashMap → LinkedHashSet; incrementing priority overload; all-memory requirements; fallback/first-valid semantics; activity transition independent of Behavior stops. |
| Behavior / BehaviorControl / running | Interface vs base class; memory/start conditions, random duration, strict timeout, default continuation, unguarded doStop; all-activity running collection and same-tick start/stop possibility. |
| Walk / Look / Attack / PATH | Typed key signatures; fixed vs live tracker representations and Vec3-to-block boundary; distinct entity/path identity and adoption/result uncertainty. |
| Transition timing / observer safety | Source caller order vs original callbacks vs sampled intervals; no observer replay of eligibility, sensor factories/scans, stateful Schedule/Timeline, custom trackers or AI. |

## What still needs integrated evidence

Existing R23 Villager evidence retains Brain/Sensor callbacks and separately sampled memory/activity state, with motion. It does not supply a complete explanation of each BehaviorControl, activity-switch reason or downstream result. Existing base-Behavior return hooks observe accepted/rejected starts and later status, but do not cover implementations that do not extend Behavior and report reason `NOT_EXPOSED`.

[R48](TYPED-BRAIN-MEMORY-2026-10-04.md) adds bounded exact-known cached WalkTarget, BlockPosTracker, EntityTracker, base Entity and Path values. Its additive six-owner/21-field ledger preserves this method-body ledger. A frozen Villager trial retains 240 snapshots, two finite original callback windows and separately sampled activity/memory/motion; it does not complete integrated causal/result evidence. Arbitrary implementations and containers remain unknown. [R49](ORIGINAL-INDEPENDENT-CONTROL-RETURN-2026-10-04.md) verifies additional concrete registration/factory/policy locators and installs original normal-return hooks for the independent OneShot/Gate bases. It retains275/68 actual native returns, while opaque trigger identity, child-parent relationships, activity-switch reasons and actual results remain unknown. The source ledger locates relevant package bodies without claiming their complete interpretation or transformed custom semantics.

A fresh private Brain trial must retain original callback ordering, instance identities, same-tick transitions, memory availability/TTL/typed target facts, active/core/default state, navigation and actual motion separately. Record caps, zero records and unknown reason/result without filling them from source expectations. Keep the original Tank read-only, freeze producer source, finalize evidence and verify shutdown/save hashes as for earlier generations.

Full path comparisons/rejections/effective cost, broader Boss battle/coordination, matched observer CPU/GPU/image measurements, actual Tank resize and the final whole-diff independent review remain in the [execution matrix](REMAINING-EXECUTION-MATRIX-2026-10-04.md). This static research is not a replacement for those acceptance items.

# YSM 2.6.5 exact distributed JAR structural scan — 2026-10-05

## 1. Exact anchor

The official Modrinth distribution has now been fixed as an exact binary anchor.

- project: Yes Steve Model
- version: `2.6.5-forge+mc1.20.1`
- Modrinth version ID: `Zqooxsd2`
- Maven coordinate: `maven.modrinth:86xjpqqS:Zqooxsd2`
- SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`
- SHA-1: `151ac7b24da8beeca1a20864565743cfd77af286`
- exact size: **63,269,843 bytes**
- ZIP entries: **1,853**
- Java class files: **955**
- YSM package class files: **955**
- classfile major version: **61 / Java 17**

The earlier Modrinth display-size value is not used as binary identity evidence.

The JAR itself was fetched in CI temporary storage, scanned, then discarded. It is not committed or
retained as a repository artifact.

## 2. Scanner boundary

Permanent reusable tool:

`departments/minecraft/mods/yes-steve-model/tools/scan_ysm_265.py`

The scanner reads only Java classfile metadata needed for structural identity:

- class name / access / superclass / interfaces;
- field name + descriptor;
- method name + descriptor;
- constant-pool strings / type references;
- selected stable external anchors.

For two narrow registration seams, bounded `javap -c -p` output was also used:

- `NetworkHandler.init()`
- the `YSMBinding` constructor.

No native devirtualization, model decryption or protection bypass was used.

## 3. Existing-map exact contract

Before expanding from the exact artifact, the 55-entry community-derived map was checked against the
official JAR.

Result:

- class targets present: 31
- exact method+descriptor targets present: 23
- exact field+descriptor targets present: 1
- failures: **0**

After the first exact-core expansion, the map reached 110 entries and again passed with 0 failures.

After the Network/Molang expansion, the map reached 185 entries and passed with:

- class targets present: 80
- exact methods present: 100
- exact fields present: 5
- failures: **0**

After the Controller/Context expansion, the map reached **210** entries and passed with:

- class targets present: **83**
- exact method+descriptor targets present: **122**
- exact field+descriptor targets present: **5**
- failures: **0**

Controller/Context-pass map confidence:

- **183 CONFIRMED**
- **27 HIGH**

## 4. Bone core recovered

The previous community pass exposed 23 readable/obfuscated bone aliases but not their owner.

The exact JAR resolves them.

### IBone

~~~text
com.elfmcys.yesstevemodel.Oo0o00oOOo0OO000000O0oO0
    -> geckolib3.core.processor.IBone
~~~

The exact class is the bone contract surface.

### AnimatedGeoBone

~~~text
com.elfmcys.yesstevemodel.OO0oo000o00O0O0oo00oO000
    -> geckolib3.geo.animated.AnimatedGeoBone
~~~

It implements the recovered IBone contract and has the artifact-era constructor shape:

~~~text
(GeoBone-like, float[], int, float[], int)
~~~

The version-matched public release-line candidate reorganizes this role as `GeoBoneState`.
That is recorded as **SOURCE_ARTIFACT_DIVERGENCE**, not forced equivalence.

The map now carries the complete public bone surface, including:

- rotation XYZ get/set;
- position XYZ get/set;
- scale XYZ get/set;
- pivot XYZ;
- absolute pivot XYZ;
- hidden / children-hidden;
- tracking;
- initial rotation;
- name / bone id.

## 5. Animatable/model/event core recovered

Exact artifact semantic identities now include:

~~~text
o0000OoOooO0oo0o0oooo0Oo
    -> AnimatableEntity

OOOO0O0O000O000000oOOO0o
    -> AnimatedGeoModel

OO00O0o0OooOOOo00OO00o00
    -> AnimationEvent

o0O0oOooOo0OoOo0oOo00O00
    -> LivingAnimatable

oo0OooOO0oOoOoOoo00oO000
    -> CustomPlayerEntity
~~~

High-value methods recovered include:

- `AnimatableEntity.getEntity`
- `getCurrentModel`
- `processAnimation(float)`
- `getBone(int)`
- `AnimatedGeoModel.getMatrixData`
- `getAbsPivotData`
- `bones`
- `getGeoModel`
- the complete main `AnimationEvent` getter/controller/data surface.

## 6. Molang context and binding recovered

### IContext

~~~text
oo0oOO0000o0Ooooo0OoOo0O
    -> IContext
~~~

The exact class access is `0x601`: a public abstract interface.

The JAR contains exactly one YSM implementor:

~~~text
O0O00Oo0o0oO0oo0oO00OOoO
    -> MolangContext
~~~

The interface/method surface recovers:

~~~text
entity
animatableEntity
mc
level
animationEvent
data
animationContext
controllerContext
random
createChild
isDebugEnabled
allowEmitting
...
~~~

### ContextBinding

~~~text
oOoOoO0O000OOoo000O0OO00
    -> ContextBinding
~~~

### YSMBinding

~~~text
oo00O000000OoOo0O0O00oOO
    -> YSMBinding
~~~

This is a particularly strong exact-artifact mapping because the class simultaneously contains:

~~~text
ground_speed2
bone_rot
bone_pos
particle
play_sound
defer
~~~

and directly extends the recovered ContextBinding.

## 7. Molang function classes recovered from constructor bytecode

The exact `YSMBinding` constructor retains literal registration names immediately followed by the
function class it instantiates.

Examples:

~~~text
bone_rot         -> BoneRotation
bone_pos         -> BonePosition
bone_scale       -> BoneScale
bone_pivot_abs   -> BoneAbsolutePivot
particle         -> ParticleFunction
abs_particle     -> ParticleFunction
play_sound       -> SoundFunction.Play
stop_sound       -> SoundFunction.Stop
stop_all_sounds  -> SoundFunction.StopAll
first_order      -> FirstOrderFunction
second_order     -> SecondOrderFunction
sync             -> Sync
defer            -> Defer
keyboard         -> InputCheck.Keyboard
mouse            -> InputCheck.Mouse
~~~

The machine-readable map contains all 25 recovered constructor pairs from this pass.

## 8. Animation controller recovered

The controller stored by the exact artifact's `AnimationEvent` is:

~~~text
oo000oooo0OOoo00O0o0OOOO
    -> PredicateBasedController
~~~

Its direct controller interface is:

~~~text
OoOoOO0O00oOoO0o0ooOO0oO
    -> IAnimationController
~~~

The exact controller's:

- two constructor shapes;
- name/predicate/interpolator/context/state fields;
- process/init methods;
- getName/current-animation;
- setAnimation overloads;
- transition configuration;
- transform visitor;
- reset/deprecated-mode behavior

match the artifact-era readable PredicateBasedController layout.

The `f184eda` release-line candidate has the evolved counterpart named `CodedAnimationController`.
This difference remains explicit.

## 9. Network layer recovered

The exact artifact class:

~~~text
OO00OoOOOOooO0ooOoOoOooO
    -> NetworkHandler
~~~

contains:

- `VERSION = "2.6.0"`;
- channel ResourceLocation;
- Forge `SimpleChannel`;
- connection AttributeKey;
- the expected channel-presence/send/broadcast helpers.

Its `init()` bytecode directly exposes registration ID -> obfuscated class.

Recovered exact table:

| ID | Semantic message |
|---:|---|
| 1 | SyncDataToClient |
| 2 | SyncDataToServer |
| 3 | ExecuteMolang |
| 4 | SyncModelInfo |
| 5 | SetModelAndTexture |
| 6 | SyncAuthModels |
| 7 | SetPlayAnimation |
| 8 | SyncStarModels |
| 9 | SetStarModel |
| 15 | SubmitRoamingVarsChanges |
| 16 | SyncProjectileModelInfo |
| 17 | SubmitRouletteConfig |
| 18 | EmitMolangSync |
| 19 | MolangSync |
| 21 | DispatchServerDrivenProperty |
| 22 | SyncVehicleModelInfo |
| 23 | EmitSwingHand |
| 51 | ServerInfo |
| 52 | ClientInfo |

Handshake classes were further distinguished by exact constructor/access and side references.

The two model-content ByteBuffer packets are also directly separated:

~~~text
O0oo00oo00OoOooO000oO00O
    -> SyncDataToClient

oo00oOo0OOO0OoOOo0O0oO0O
    -> SyncDataToServer
~~~

The server-directed variant uniquely references `ServerPlayer`.

This recovers the Java transport envelope while leaving the native model-sync protocol body outside
the research boundary.

## 10. What exact-artifact scanning changed

Before this pass, a public source candidate or compatibility project could strongly suggest a
semantic identity.

Now the exact artifact can answer a different question:

> Does this exact class/member/descriptor actually exist in the official distributed 2.6.5 JAR?

This lets KNEEKURA separate:

~~~text
semantic comparison
from
binary structural truth
~~~

without pretending the public source candidate is the build input used to produce the release.

## 11. Failure preserved during the scan

The first CI scan successfully downloaded and hashed the exact JAR but failed to emit
`structure.json`.

Cause:

- the new Python scanner defined `main()`;
- its first committed version forgot the `if __name__ == "__main__": main()` entry point.

Repair:

- add the explicit entrypoint;
- rerun against the same exact Modrinth artifact;
- retain the failed run as workflow history.

This is a useful small example of KNEEKURA's failure-preservation rule: a failed evidence pipeline is
not silently rewritten into a successful history.

## 12. Remaining boundary

Still not claimed:

- complete semantic recovery of all 955 classes;
- exact build transformation that produced the distributed JAR from public history;
- protected native renderer implementation;
- native model-sync protocol body;
- encrypted model/container internals.

Those unknowns do not block reuse of the recovered Java architecture.

## 13. Current structural chain

The exact artifact now supports a direct high-confidence chain:

~~~text
Minecraft Entity
   |
   v
AnimatableEntity / LivingAnimatable
   |
   +--> AnimationEvent
   |
   v
MolangContext : IContext
   |
   v
YSMBinding : ContextBinding
   |
   +--> Molang function / side-effect classes
   |
   v
PredicateBasedController : IAnimationController
   |
   v
AnimatedGeoModel
   |
   v
IBone / AnimatedGeoBone
   |
   v
NativeRenderer.renderModel(...)
   |
   v
protected/native geometry backend

and independently:

NetworkHandler
   |
   +--> IDs 1..23 transport / state messages
   |
   +--> 51 ServerInfo
   +--> 52 ClientInfo
   |
   +--> ByteBuffer model-sync envelopes
~~~

That is enough to treat the 2.6.5 Java shell as a partially recovered architecture rather than an
opaque obfuscated blob.


## 14. Previous bounded continuation (253 mappings)

Fresh official Modrinth Zqooxsd2 acquisition reproduced SHA-256/SHA-1/size before analysis. The
232-entry baseline reproduced 97 classes / 130 methods / 5 fields with 0 failures. After five class seeds and
sixteen bounded methods, that milestone result was:

- **253 mappings (216 CONFIRMED / 37 HIGH)**;
- **102 class targets / 146 exact methods / 5 exact fields**;
- **0 failures / 0 parse errors / 0 duplicate IDs / 0 duplicate owner+member+descriptor keys**;
- **102 semantic seeds** and an unchanged 955-class, 3,618-edge, 19-component graph.

The dossier records exact flags/descriptors, order-independent normalized declaration predicates,
1/955 candidate matches for each seed, typed nesting and selected Java field/call-reference paths.
Animation remains HIGH with explicit source divergence; Molang matches the pinned official source
surface but does not establish whole-binary equivalence. Ambiguous overloads are preserved.

`javap` was unavailable locally. A bounded classfile reader replaces it for these five Java owners;
this is recorded as a tool limitation, not a runtime verification. Source/hash/call evidence is
retained in [SEED-RECOVERY-EVIDENCE-2026-10-05.json](SEED-RECOVERY-EVIDENCE-2026-10-05.json).

Reproduce with an official JAR held outside the repository:

```bash
python tools/scan_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-scan.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence SEED-RECOVERY-EVIDENCE-2026-10-05.json --out /scratch/ysm-seed-audit.json
python tools/cluster_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-foundation.json
```

Commands run from the YSM research directory. The structural contract does not replace semantic
review, and no Minecraft/native runtime correctness or performance result is claimed.


## 15. Molang evaluation continuation

The current map has **270 mappings (233 CONFIRMED / 37 HIGH)**: **105 classes / 160 methods /
5 fields**, with **0 failures**. This pass adds ExecutionContext, Expression and ValueConversions plus
14 methods, including the two previously ambiguous integer ArgumentCollection accessors.
Expression has two normalized declaration candidates; the independently grounded getExpression
return-type relation reduces this to one. Context wrappers catch Exception and return null; converter
branch/reference behavior establishes primitive/string semantics. CONFIRMED denotes semantic
correspondence, with original symbol spelling unproven and SOURCE_ARTIFACT_DIVERGENCE preserved.

Fresh audits: old seed **66 / 0**, evaluation **106 / 0** checks/failures. Relation, branch target, catch
type and code digest negative mutations each fail. Foundation now uses **105 seeds**; the graph remains
955 classes / 3,618 edges / 19 components with 15 isolated UNKNOWN classes. Three pinned Chinese
primary repositories provide fixture/provenance leads but no exact-version mapping promotions.

See [MOLANG-EVALUATION-RECOVERY-2026-10-05.md](MOLANG-EVALUATION-RECOVERY-2026-10-05.md) for
exact identities, behavior, source/version separation, failure history and rerun commands, and
[MOLANG-EVALUATION-EVIDENCE-2026-10-05.json](MOLANG-EVALUATION-EVIDENCE-2026-10-05.json) for
the retained machine-readable dossier. This closes the selected small cluster; broader evaluator
implementation and runtime checks remain future work.

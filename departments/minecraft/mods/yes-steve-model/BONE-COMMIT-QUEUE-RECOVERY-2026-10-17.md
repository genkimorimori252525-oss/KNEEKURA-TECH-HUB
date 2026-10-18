# Bone commit and queue-consumer continuation — 2026-10-17

## Bounded result and review status

This pass follows the independently reviewed AnimationProcessor lifecycle into the
snapshot commit, animation-vector application and all three direct implementations
of the queue-consumer interface. **Thirteen method mappings are reviewed and integrated**: one commit, three AnimationVec3 mutators and nine
poll methods. Constructors, record boilerplate, getters and support snapshots are
not promoted to increase counts. Central mappings are not changed by this dossier.

The evidence retains **53 complete method records across eight owners**, including
four abstract declarations with no fabricated Code body. Thirteen selected methods
have reviewed local semantics; forty records supply context/support. This is not a
claim that all 53 methods have received complete semantic recovery.

- Exact Modrinth artifact `Zqooxsd2`: SHA-256
  `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`,
  63,269,843 bytes. Artifact remains outside Git.
- Official candidate source is pinned to
  [`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6).
  Nine source-file hashes and URLs are retained in the dossier.
- Whole source/artifact equivalence remains **NOT_ESTABLISHED**. Global
  **SOURCE_ARTIFACT_DIVERGENCE** and the prior BoneAnimationQueue item-level flag
  remain preserved. No new local control-flow mismatch was found in the selected
  bodies against the pinned candidate. This does not clear historical flags or
  establish equivalence of the entire controller/queue implementation.
- Semantic method labels are research correspondences, not proven original names.

## Exact connected owners

All names below share `com/elfmcys/yesstevemodel/`.

| Research counterpart | Exact suffix | Complete methods |
|---|---|---:|
| BoneTopLevelSnapshot | `oOO0o0oOOOoOoo00oOO0Oo00` | 2 |
| BoneSnapshot (support) | `O0oOOO0o0OoO0Oo0OOOoOoOo` | 5 |
| AnimationVec3 | `OO00000oOOOoO0o00o00OOo0` | 6 |
| BoneAnimationQueue state | `oooO000oOoOooooOooo00oOO` | 11 |
| IBoneAnimationQueue | `O0OO0Oo0Oo0O0oOO0OOoO000` | 4 abstract |
| Bedrock BlendBoneAnimationQueue | `O00Oo0oo0Ooo0oOOOo0OO0oO$o0OOooo0o0OO00OoOOOo0o0O` | 11 |
| Coded SingleBoneAnimationQueue | `oo000oooo0OOoo00O0o0OOOO$Oo0Oo0o00O00Oo0OOoOOoooo` | 9 |
| VehicleOriginController AnimationQueue | `oo0Oo0O00oooOoOo0O0oOOOo$Oo0Oo0o00O00Oo0OOoOOoooo` | 5 |

The interface's exact declarations distinguish snapshot getter and rotation,
position and scale Optional-returning consumers. An exact-artifact declaration
scan found these three direct implementors. Inherited/runtime-generated or future
implementors are not ruled out. Ten exact processor callsites connect the prior
cohort to these snapshot/interface/vector operations. Full declarations and
BootstrapMethods for all eight owners, plus the referenced IBone declaration,
are retained. Source field names alone do not substitute for those identities.

## Commit: ordered writes, not an atomic transaction

BoneTopLevelSnapshot.commit is exact `Oo0Oo0o00O00Oo0OOoOOoooo()V`.

1. Hidden and children-hidden flags go to IBone at offset 12.
2. The initial rotation vector is read at 21.
3. Rotation X/Y/Z add snapshot offset to initial X/Y/Z (`fadd` 42/63/84) and
   call the respective setters at 43/64/85.
4. Position X/Y/Z pass snapshot components directly at 101/117/133.
5. Scale X/Y/Z pass snapshot components directly at 149/165/181.
6. Cached rotation point data is set to `(0,0,0)` at 193, after all bone calls.

There are no handlers or rollback steps. A setter exception can leave earlier
writes applied and skip later writes/cache reset. This is an instruction-path
possibility, not proof of an in-game defect. IBone implementations and native
rendering outcomes are not established here. The superclass support captures
rotation relative to initial rotation, consistent with the offset added at commit;
no standalone superclass method mapping is proposed in this pass.

## AnimationVec3: transition fraction and destination aliasing

All constructors initialize `endingTransitionPercentProgress` to float 1.
The updater `(F)V` uses `fcmpg` at 5 and `ifge` at 6 to skip the write at 11 unless
the supplied argument is strictly smaller. This is a minimum-only update, not a
clamp into [0,1]. Negative values may be stored; NaN does not win the comparison.
A preexisting NaN field also prevents an update through this method. The public
field can be written by other code, so this method is not a global invariant.

`apply(Vector3f)` and `applyRotation(Vector3f,Vector3f)` test the stored fraction
against zero with `fcmpl`/`ifne` at 7/8. Both signed zero values use direct
`dst.set(this)` at 13. Otherwise:

- apply calls the exact vector interpolation helper at 24 with
  `(fraction, this, dst, dst)`.
- applyRotation calls the different helper at 25 with
  `(fraction, this, dst, initialRotation, dst)`.

The old destination is also the output argument. NaN takes the delegated path.
These wrapper findings do not assume clamping, generic linear rotation or a
particular helper implementation. MathUtil interpolation is a separately bounded
continuation, not inferred merely from the method name.

## Poll methods read points; they do not dequeue them

The nine concrete poll bodies have no local handlers and no writes removing their
stored queue point fields. Despite the names, repeated calls can encounter the same
stored point. Callees can evaluate expressions or mutate data; this is not a purity
or exactly-once claim.

### SingleBoneAnimationQueue

All three methods first read the corresponding point field. Null branches at 9
return Optional.empty at 12. Non-null paths return an AnimationVec3 at the end.

- Rotation distinguishes ending, beginning and ordinary points. Ending points use
  their interpolated vector and progress, then apply weight. Beginning points get
  a destination and multiply it by queue weight before rotation interpolation at
  137, using transition offset and initial bone rotation; output progress becomes
  zero. Ordinary points get an interpolated vector, apply weight, then progress zero.
- Position and scale get the point vector, then distinguish ending progress from
  beginning/ordinary paths. Beginning changes the weight through the referenced
  scalar interpolation at 84; non-ending sets output progress zero at 91.
- Position uses vector multiplication at 104. Scale instead calls the weighted-scale
  helper at 105 with the same vector as input/output. They are not interchangeable.

There is no local guarantee that point evaluation returns a non-null finite vector;
point-generation and interpolation behavior remain delegated.

### BlendBoneAnimationQueue

Every iteration first checks the pair's condition, then queue active state, then
its selected point for non-null. Rotation's decisive gates are 69, 92 and 107;
position uses 66, 89 and 104; scale uses 69, 92 and 107. Rejected entries loop onward.
If no point is accepted, the final branch returns Optional.empty.

The **first accepted** point fixes beginning-transition mode and captures offset /
progress (plus initial rotation for rotation). This is not reselected for each
subsequent queue. Outside beginning mode, ending points reduce their contribution
weight by `(1-progress)` and update the minimum output fraction; other points set
the fraction to zero. Rotation/position accumulate weighted `fma` from zero. Scale
starts at `(1,1,1)` and multiplies either the point or a weighted-scale result.
No normalization by summed weights is performed locally.

In beginning mode, the exact comparisons are `progress <= -1e-5f` OR
`progress >= +1e-5f` (retained float constants are approximately ±0.000009999999747).
Outside or on those bounds, each accepted point is checkcast to the beginning-point
class and its destination contributes. Inside the strict band, the method copies
the offset and immediately returns, skipping later entries and final interpolation.
NaN also takes this early-return branch because both ordered comparisons are false.

The cast for later accepted entries has no new instanceof guard. It is therefore
important not to assume heterogeneous queues are safe: producer guarantees about
homogeneous transition point types remain a separate open question. This is not a
reproduced ClassCastException. After the loop, an active beginning-mode result
passes through the relevant interpolation helper before Optional.of.

### Vehicle queue

Rotation returns Optional.ofNullable of the outer controller's existing rotation
object, without copying or consuming it. Position and scale always return
Optional.empty. This queue's return identity differs from the newly allocated
AnimationVec3 objects in the single/blended consumers.

## Verification and limits

Fresh custom audit: **371 checks, zero failures; 19 corrupt-evidence controls all
reject**. The tool fixes artifact hash/size, the 53-method identity set, eight owner
snapshots, nine source path/hash records and ten processor callsite records. Every
present code record requires instructions, complete operands, handlers and code
hash; abstract interface methods must lack Code fields. Bootstrap/declaration/source
omissions cannot silently shrink the scope.

Controls include missing owner/method/source/boundary/bootstrap records, changed
rotation add/reset, invented commit handler, NaN comparison direction, zero-path
polarity, output alias, null/condition/epsilon gates and weighted-scale target.
These are static corrupt-evidence rejection tests, not execution of a mutated JAR
or semantic tests of a running game. The descriptions above were separately read
against the exact instruction paths and pinned source. Independent review passed for the stated local Java semantics.

```bash
python tools/bone_commit_queue_ysm_265.py \
  --jar /absolute/path/to/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence BONE-COMMIT-QUEUE-EVIDENCE-2026-10-17.json \
  --out /absolute/path/outside/repo/bone-audit.json
```

## Continuing roadmap

This is one checkpoint in the ongoing recovery, not an overall stopping point.

1. Close exact MathUtil interpolation and AnimationPoint beginning/ending/keyframe
   contracts, especially aliasing, progress bounds and exception/context behavior.
2. Trace controller/player point producers and reset/activation transitions to test
   whether blended beginning-point casts have a proven homogeneous input invariant.
3. Follow IBone Java implementations for individual setter writes and dirty-state
   propagation; keep native renderer/model protection boundaries explicit.
4. Reconcile source-era differences owner by owner and promote only supported
   methods after independent review. Do not equate map counts with completion.

Raw JARs, source trees and decompiled source are not published. No target execution,
native/protection/decryption work, runtime bug claim or performance measurement was
performed in this pass.

## Integrated checkpoint

This cohort passed independent static review and is included in the 662-mapping
checkpoint. See [verification](ANIMATION-PIPELINE-VERIFICATION-2026-10-17.json).
The continuing research queue remains active; runtime and whole-source equivalence
are not established.

## October18 bounded producer-invariant update

[Producer→consumer subtype proof](BEDROCK-QUEUE-PRODUCER-INVARIANT-2026-10-18.md) now establishes sufficient synchronized, stable-data conditions for the exact built-in linear and segmented transitions. This is conditional rather than universal safety: missing-animation exclusion additionally requires null pending nextAnim, because resetToIdle does not clear it. External mutation/reentry and arbitrary transition implementations remain outside the proof; equal progress is not inferred.

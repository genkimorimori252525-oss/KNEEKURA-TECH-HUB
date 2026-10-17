# AnimationPoint progress, context and cached-result boundary — 2026-10-17

## Bounded checkpoint

This continuation follows the reviewed queue consumers into their four point owners.
It adds **seven method mappings**, independently reviewed and integrated. Four constructors,
two direct field getters and one abstract method are support, not mapping inflation.
All **14 method declarations/bodies** are retained. The exact JAR has three direct
subclasses of the abstract point owner; this observation does not rule out runtime
or future subclasses.

Artifact: Modrinth `Zqooxsd2`, SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`,
63,269,843 bytes. Source: official release-line candidate at
[`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6),
with four exact paths/hashes/URLs retained. Whole-source equivalence and original
names remain unproven; global SOURCE_ARTIFACT_DIVERGENCE is preserved. No mismatch
was found in these bounded local paths against that candidate.

Exact owners, all under `com/elfmcys/yesstevemodel/`:

| Research role | Exact suffix | Methods |
|---|---|---:|
| AnimationPoint | `oO0O00Oo00o00OO0o0OOOOOO` | 4 (one abstract) |
| BeginningTransitionPoint | `O0O0O00OOO0o00o00ooooOo0` | 5 |
| EndingTransitionPoint | `Oo0oooOOoo00ooOO00OO0OO0` | 3 |
| KeyFramePoint | `O00ooo0O0Ooo0OOO0oo00o0o` | 2 |

The evidence includes complete fields, superclass links and empty bootstrap/handler
records where applicable. The labels are semantic research correspondences, not
proof that the distributed binary retained these original names.

## Duration-zero behavior is different for ending points

Base getPercentCompleted compares totalTick with float zero at offsets 5/6. Either
signed zero returns float **1** at 9; otherwise it divides currentTick by totalTick
at 21. There is no clamp, positive-duration validation or finite-value check.

EndingTransitionPoint overrides that method. Total-zero check 5/6 leads to a second
current-zero check 14/15: zero current yields **0** at 18, otherwise **1** at 22.
Nonzero total uses division at 32. Both signed zeros compare equal. With zero total,
NaN current follows the nonzero branch and returns 1; NaN total reaches division.
For finite nonzero durations, negative and beyond-duration progress remain possible.
These are static JVM numeric-path observations, not executed animation fixtures.

BeginningTransitionPoint separately stores a constructor-supplied transition fraction.
Its interpolation uses that field, not an implicit call to base getPercentCompleted.
The accessor simply returns the supplied fraction; this class does not locally
clamp it or validate its relationship to currentTick/transitionLength.

## Context setup overwrites; it does not restore

Base setupAnimationContext calls evaluator.entity at 1, casts at 6, reads its stored
animation context at 10, and invokes the context setter at 13. It saves no previous
context, performs no null guard and has no exception handler.

Beginning getLerpPoint, beginning getTransitionDst and keyframe getLerpPoint invoke
that setup before their delegated evaluation. An escaping downstream exception does
not restore prior context locally. The previously reviewed processor clears context
at its ordinary tick tail, not a guaranteed finally. This is a bounded lifecycle
observation; actual exception reachability and higher caller recovery remain separate.

Ending getLerpPoint does **not** invoke setup and does not read its evaluator argument.
It merely reads the stored source vector, refreshes cached coordinates and returns
that source. Do not infer that every point installs its own context before returning.

## lastLerpResult is refreshed after evaluation, not memoization

### Beginning getLerpPoint

Setup is at 2; delegated transition destination generation at 10. The exact MathUtil
vector helper at 24 receives `(storedFraction, offsetPoint, dst, dst)`. The destination
is both interpolation input and output. Only after that does the cache-null branch
at 31 allocate a Vector3f copy (40/write43) or update the existing cache (54).
The method returns the original destination at 59, **not** the cached-copy field.

Beginning getTransitionDst performs setup at 2 then directly returns the delegated
destination (call10/return13). This accessor neither interpolates nor updates the
lastLerpResult cache. The offset getter likewise returns the stored reference, with
no defensive copy.

### Ending getLerpPoint

Cache-null branch 4 creates a copy of srcPoint (16/write19), otherwise set33 updates
the existing cache. Return41 returns the original stored srcPoint reference. There
is no expression evaluation, interpolation or time-progress multiplication here;
ending transition contribution is handled by the previously reviewed consumers.

### KeyFrame getLerpPoint

Setup2 precedes inherited progress11, passed to the exact keyframe call14. Only after
that returned value is obtained does cache-null22 allocate31/write34 or update45.
Return50 is the original generated result. Every call reaches the keyframe generator
before checking the cache. This is not an evaluate-once cache.

All three implementations allocate on an initially null cache and reuse an existing
cache vector otherwise. Because the cache field is publicly accessible, this is not
a global non-aliasing or immutability guarantee. Delegates may return aliases or
throw; no non-null/fresh-vector guarantee follows from these point wrappers. No local
handlers protect cache refresh or return, so failures can leave the previous cache.

## Dependency and acceptance boundary

Exact references identify the next calls but do not close their semantics:

- Transition destination owner `OooOo0o00OO00O000oOOo0O0` with
  `(L.../O0Oooo00oOo00O00OoOOOooO;)Lorg/joml/Vector3f;`.
- BoneKeyFrame owner `OOOo0OooOOoOooooooo000O0` with
  `(L.../O0Oooo00oOo00O00OoOOOooO;F)Lorg/joml/Vector3f;`, and its duration getter.
- Interpolation calls link to the separately reviewed MathUtil cohort. External JOML
  implementation/numeric equivalence and later easing behavior are not inferred.

Fresh custom verification: **109 checks, zero failures; 16 corrupt-evidence controls
all reject**. Checks require the exact artifact, complete 14-method/four-owner sets,
mandatory code operands/handlers or abstract absence, all bootstrap records, four
fixed source path/hash records and checkout revision. A full 955-class declaration
scan independently verifies the three direct subclasses.

Negative controls cover omitted evidence/source/owner records, base versus ending
zero-result differences, zero-duration branching, context setter identity, cache
branch, interpolation output alias, wrong returned field, keyframe target and
invented finally handler. These are evidence-regression checks, not target execution
or proof of semantic prose. Independent review passed for these bounded local claims.

```bash
python tools/animation_point_ysm_265.py \
  --jar /absolute/path/to/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence ANIMATION-POINT-EVIDENCE-2026-10-17.json \
  --out /absolute/path/outside/repo/point-audit.json
```

## Next connected work

Continue into TransitionKeyFrame/BoneKeyFrame implementations and their expression /
easing inputs. Then trace controller/player point producers for the blended queue's
beginning-point homogeneity assumption and timing/reset decisions. This checkpoint
does not end the user-requested ongoing recovery or establish whole-YSM completion.
No target execution, native/protection work, raw artifact/source publication, runtime
bug reproduction or performance measurement occurred here.

## Integrated checkpoint

This cohort passed independent static review and is included in the 662-mapping
checkpoint. See [verification](ANIMATION-PIPELINE-VERIFICATION-2026-10-17.json).
The continuing research queue remains active; runtime and whole-source equivalence
are not established.

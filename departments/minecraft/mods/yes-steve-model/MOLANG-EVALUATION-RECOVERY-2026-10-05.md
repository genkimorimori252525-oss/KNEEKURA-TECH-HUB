# YSM 2.6.5 bounded Molang evaluation recovery — 2026-10-05

This continuation adds **3 classes and 14 methods** to the published 253-row baseline
`225428d05fae385d1ada3b5ba9f6ee74c86761b0`. The current map has **270 mappings: 233 CONFIRMED /
37 HIGH**, with **105 class / 160 method / 5 field** contracts and **0 failures**.
CONFIRMED means supported semantic correspondence; recovered original symbol spellings remain
unproven. The global **SOURCE_ARTIFACT_DIVERGENCE** finding and **NOT_ESTABLISHED** binary/source
equivalence remain unchanged. All 253 prior mapping rows are preserved.

## Bounded result

The selected chain is Function arguments → ExecutionContext → Expression visitor entry →
ValueConversions. A caller can obtain the stored expression, evaluate through an unsafe context
entry, then convert the resulting Object. The two default context wrappers catch `java/lang/Exception`,
log `Failed to evaluate molang expression.`, and return null; they do not catch every Throwable.
No evaluator implementation or parser traversal was added in this pass.

| Exact class owner suffix | Semantic counterpart | Candidate result |
|---|---|---|
| `oO0OoO0O0OoO0oo0oo0OOooo` | `ExecutionContext` | 1 / 955 |
| `oOOOOoo0O0Oo0O00oo0oooO0` | `Expression` | 2 → 1 by known getExpression return type |
| `OO0O00ooOo0OO0oooOoo0Oo0` | `ValueConversions` | 1 / 955 |

Declarations use access flags, supertype/interfaces and order-independent field/method multisets.
YSM descriptor types are erased to `LYSM;` for the initial whole-JAR comparison. ExecutionContext
and ValueConversions each have one match among 955 classes. Expression has **two** shape matches;
the previously CONFIRMED ArgumentCollection.getExpression `(I)L…Expression;` return descriptor
selects one. The prior accessor is independently grounded by its List.get/cast/direct-return path,
so this relation does not assume the new Expression identity. The typed visit descriptor is retained;
the separate visitor's full dispatch surface is not claimed as an automated audit result.

## Exact method identities

Class owners are recorded above and in the JSON dossier. Method names are meaningful only together
with their exact owner and full JVM descriptor.

| Semantic method | Exact member | Full descriptor |
|---|---|---|
| `ExecutionContext.entity` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `()Ljava/lang/Object;` |
| `ExecutionContext.evalSingleExpressionUnsafe` | `o0OOooo0o0OO00OoOOOo0o0O` | `(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;` |
| `ExecutionContext.evalMultiExpressionUnsafe` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Ljava/lang/Iterable;Z)Ljava/lang/Object;` |
| `ExecutionContext.evalSingleExpression` | `O00OOOooOoooOoo0o0o0oO0O` | `(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;` |
| `ExecutionContext.evalMultiExpression` | `o0OOooo0o0OO00OoOOOo0o0O` | `(Ljava/lang/Iterable;Z)Ljava/lang/Object;` |
| `Expression.visit` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Lcom/elfmcys/yesstevemodel/Oo0000oo0oo0OoO00000O0O0;)Ljava/lang/Object;` |
| `ValueConversions.asBoolean` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Ljava/lang/Object;)Z` |
| `ValueConversions.asFloat` | `o0OOooo0o0OO00OoOOOo0o0O` | `(Ljava/lang/Object;)F` |
| `ValueConversions.asInt` | `O00OOOooOoooOoo0o0o0oO0O` | `(Ljava/lang/Object;)I` |
| `ValueConversions.asDouble` | `oOOOo0OOO0ooooo0O00OO0o0` | `(Ljava/lang/Object;)D` |
| `ValueConversions.asString` | `OOOOo0O0oO0OOo0O0O0Oo0O0` | `(Ljava/lang/Object;)Ljava/lang/String;` |
| `ValueConversions.asPooledString` | `Ooooo0oooO0oooOOOoO0000O` | `(Ljava/lang/Object;)I` |
| `Function$ArgumentCollection.getAsPooledString` | `o0OOooo0o0OO00OoOOOo0o0O` | `(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I` |
| `Function$ArgumentCollection.getAsInt` | `oOOOo0OOO0ooooo0O00OO0o0` | `(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;I)I` |

## Conversion behavior supported by Java bytecode

| Conversion | null | Number | Boolean | Other objects |
|---|---|---|---|---|
| asBoolean | false | float value; NaN/zero false | underlying value | true |
| asFloat | 0 | float value; NaN becomes 0 | 1 / 0 | 1 |
| asDouble | 0 | double value; NaN becomes 0 | 1 / 0 | 1 |
| asInt | 0 | Number.intValue; no explicit NaN branch | 1 / 0 | 1 |

Non-NaN signed floating zero is retained by the float/double paths. `asString` returns a String
unchanged or reads StringExpression's string getter; other values, including null, return null.
It does not stringify arbitrary Objects. `asPooledString` uses StringExpression's integer getter,
StringPool's `computeIfAbsent`-backed String entry, or the exact `EMPTY` fallback field. This pass
does not assert the numeric value of that fallback.

The two integer-return ArgumentCollection accessors were ambiguous by descriptor alone. Their
terminal invokestatic at offset 19 now distinguishes `getAsInt` from `getAsPooledString`, using the
independently resolved converter behavior. StringExpression/StringPool method instructions are
bounded supporting evidence, with no additional class mapping promotions.

## Pinned source and Chinese primary reconnaissance

Official release-line comparison uses
[f184edabd1b5115ce5a24cb6d155ba5a669f5ba6](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6),
including ExecutionContext, Expression, ExpressionVisitor, Function, ValueConversions,
StringExpression and StringPool. Exact paths, immutable URLs and file hashes are in
[MOLANG-EVALUATION-EVIDENCE-2026-10-05.json](MOLANG-EVALUATION-EVIDENCE-2026-10-05.json).
The previously pinned OpenYSM track remains comparative; this pass does not promote it to artifact truth.

Fresh Chinese creator/compatibility repositories were inspected at immutable revisions:

| Primary source | Revision | Declared version track | Outcome |
|---|---|---|---|
| [Anan1a/YSM-molang-functions](https://github.com/Anan1a/YSM-molang-functions/tree/1c027e56d1ade400ed6abb3d23068b2b6d1a469c) | `1c027e56d1ade400ed6abb3d23068b2b6d1a469c` | YSM / Minecraft / loader all unspecified | Creator-language fixture leads; no Java identities. |
| [lin114810/ysm-vivecraft-compat](https://github.com/lin114810/ysm-vivecraft-compat/tree/04ab2ad83a8f19f3746079c2cfe823431a191a26) | `04ab2ad83a8f19f3746079c2cfe823431a191a26` | 2.5.1 in gradle.properties; README 2.5.1+; mods.toml [2.5,); 1.21.1; NeoForge 21.1.172 configured | Speculative optional hook; no full contract. |
| [Fox-TerribleCoding/YES_SlashBlade](https://github.com/Fox-TerribleCoding/YES_SlashBlade/tree/3b47cae18149a7a2de551e819ad9a00aae305aaf) | `3b47cae18149a7a2de551e819ad9a00aae305aaf` | 2.6.5-neoforge+mc1.21.1-release.jar; README fingerprint prefix B285C73D4EC010D9, 63463229 bytes, community-reported; 1.21.1; NeoForge 21.1.x; build.ps1 lists 21.1.248 | Precise adjacent animation contracts; different artifact. |

Anan1a's actual scripts read args, return temporary structures and call nested fn functions. They
supply future runtime fixture ideas, without establishing version provenance, Java owners, or aliasing
semantics. Vivecraft's bare eval target, `require=0` and first-matching-field reflection are a useful
negative control: a plausible integration claim is not an exact contract. YES_SlashBlade's full
obfuscated descriptors and artifact fingerprint are stronger neighboring evidence, but its
NeoForge 1.21.1 animation context is not this Forge 1.20.1 Molang ExecutionContext. Its maintainer's
22-type/34-member verification claim was not reproduced; its build script is a normal javac/jar build.
**Zero mappings were promoted from community evidence.**

The [Chinese script documentation](https://ysm.cfpa.team/wiki/molang/script/) and
[index](https://ysm.cfpa.team/wiki/molang/index/) yielded search snippets only; direct reads timed out.
Indexed recursion/null/structure claims remain leads, not exact 2.6.5 findings. An additional broad
search returned unrelated results. No protected parser/native/protection repository was inspected.

## Verification and reproduction

The exact JAR hash, SHA-1 and 63,269,843-byte size were rechecked before analysis. Fresh full scanner:
270 contracts, 955 classes, zero contract/parse failures. Fresh old seed audit: **66 checks / 0 failures**.
Fresh evaluation audit: **106 checks / 0 failures**, covering three declarations, fourteen member
paths and bounded supporting dependency methods. Foundation: **105 seeds**, unchanged **955 nodes /
3,618 undirected edges / 3,823 directed references / 19 components**; 15 isolated UNKNOWN classes remain.

The audit verifies flags/full descriptors, declared shape relations, ordered references, selected
full opcode/branch-target sequences, code digests and exception tables. Semantic comparison against
pinned source is separately reviewed. No Minecraft/Molang runtime execution or performance result
is claimed. It requires an official artifact outside the repository:

```bash
python tools/scan_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-scan.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence SEED-RECOVERY-EVIDENCE-2026-10-05.json --out /scratch/ysm-seed-audit.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence MOLANG-EVALUATION-EVIDENCE-2026-10-05.json --out /scratch/ysm-evaluation-audit.json
python tools/cluster_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-foundation.json
```

Run from the YSM directory. Negative controls each exited 1: replace Expression's getExpression
anchor descriptor with `(I)Ljava/lang/Object;`, increment the first retained branch target, replace
the first exception catch type with java/lang/RuntimeException, or replace a member code digest with
64 zeros. Each triggers its corresponding relation/control-flow/handler/digest failure.

The first new audit failed with KeyError because it inventoried only new class owners; two new
member rows belong to the previously mapped ArgumentCollection. The minimal repair inventories
class/member/support owner union. Those two rows now serve as the normal rerunnable regression
case; no duplicate class seed was added. The first delegated reconnaissance model was unavailable
and was replaced by the authorized Sol model; completed pinned records were integrated.

The next bounded opportunity is the concrete ExecutionContext evaluation/visitor implementation,
with the creator scripts as possible fixture leads. It remains outside this completed milestone.

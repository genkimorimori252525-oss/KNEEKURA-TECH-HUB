# Practical Java semantic recovery milestone — 2026-10-05

**604 semantic mappings:340 CONFIRMED / 264 HIGH;294 class roles,302 methods and 8 fields.** The previous 282 rows are unchanged. This campaign adds 187 class roles,132 methods and 3 fields. Original unobfuscated symbols remain unproven.

## Meaning recovered

| Connected surface | New classes | New methods | New fields |
|---|---:|---:|---:|
| [MOLANG-LOOP](MOLANG-LOOP-EVIDENCE-2026-10-05.json) | 2 | 9 | 3 |
| [BROAD-ROLE](BROAD-ROLE-EVIDENCE-2026-10-05.json) | 20 | 36 | 0 |
| [BROAD-FOLLOWUP](BROAD-FOLLOWUP-EVIDENCE-2026-10-05.json) | 6 | 12 | 0 |
| [MOLANG-MATH](MOLANG-MATH-EVIDENCE-2026-10-05.json) | 28 | 54 | 0 |
| [MOLANG-POOLED-PARSER](MOLANG-POOLED-PARSER-EVIDENCE-2026-10-05.json) | 10 | 21 | 0 |
| [BROAD-POOL](BROAD-POOL-EVIDENCE-2026-10-05.json) | 84 | 0 | 0 |
| [MOLANG-TYPED-AST](MOLANG-TYPED-AST-EVIDENCE-2026-10-05.json) | 18 | 0 | 0 |
| [SOURCE-HINT-FOLLOWUP](SOURCE-HINT-FOLLOWUP-EVIDENCE-2026-10-05.json) | 19 | 0 | 0 |

- Loop and foreach builtin registration reaches exact evaluator bodies; continue/break consumption, assign-before-body and protected-region depth cleanup are retained. Cleanup rethrows escaping exceptions; initialization before protected regions is not promised cleanup. Loop count rounds then caps at 1024, without a lower clamp.
- MathBinding closes 31 names over 27 unique implementations, including aliases. Thirteen function bodies and all 27 arity predicates have local CONFIRMED semantics;14 bodies remain HIGH where Minecraft SRG or utility correspondence is unproven. Random accepts 2/3 arguments but ignores the third; integer endpoints use difference without+1. pi/e constructor literals are boxed Double, then inherited constValue converts Number to Float before storage.
- Pooled string/property stores and parser/lexer lifecycle wrappers connect input streams to expression dispatch; HashMapStruct right-value copies share their map while the other branch clones it. No whole grammar, deep-copy or runtime concurrency guarantee.
- All concrete typed AST roles connect constructors, typed accessors/visitor dispatch and known evaluator consumers. Operation enums use retained names and exact initializer precedence/index values; complete binary-evaluator lambda semantics remain outside this pass.
- Controller collections/discovery/conditions, animation state, GUI/config, compatibility adapters, renderer/model utility roles and command frontends receive source-grounded HIGH class labels. Lambda execution claims retain actual BootstrapMethods handles; constructors are support evidence, not count inflation.

The remaining 18 concrete source leads hidden by graph-domain labels have also been actually compared: Curios/Swem/TLM bindings, AnimationProcessor, primary/user-function bindings, parser/token/vector/engine/debug families. All 18 receive class-only HIGH roles with zero actual native members; source comments alone are not native declarations. The inspected AnimationUtils singleton supplies one additional HIGH class. Previous 585 rows are preserved.

## Remaining surface and stopping point

| Exact artifact region | Classes | Mapped roles | Still unseeded |
|---|---:|---:|---:|
| Main YSM/modified runtime component |722|290|432|
| Bundled Concentus and VorbisJava |217|3|214|
| Isolated components |16|1|15|
| Total |955|294|661|

The 16 singletons comprise 15 UNKNOWN and one RENDERER structural hint. The latter now has a class-only HIGH AnimationUtils counterpart: independently sourced static float divide/multiply 20 helpers and typed Entity→EntityRenderer wrapper. Source/hash/full body support is retained; external SRG correspondence remains caveated. Earlier 618+214+15 baseline accounting omitted this one singleton; the 848 overall unseeded total was already correct. Graph topology did not change; final 432 main+214 media+15 unseeded singletons=661.

All 618 initially unseeded main owners were screened against declaration shapes, external descriptors, exact literals, known seeds and 828 pinned official Java files. The finite 101 literal+8 relational leads all received source/semantic dispositions:90 accepted (including six GUI followups) and 19 explicit other outcomes. The first broad 20 and connected 58 Molang roles supplement that pool; all 18 additional concrete source candidates and one singleton were then grounded. This is detailed comparison of the selected owners, not semantic inspection of every graph-hint class.

The remaining 432 main owners retain owner-level reasons in [SEMANTIC-COVERAGE-2026-10-05.json](SEMANTIC-COVERAGE-2026-10-05.json): ambiguous/shared literal matches, weak external descriptors, unvalidated graph-only hints, no exact source anchor, explicit native/protection/media boundaries, and low-information DTO/anonymous/presence leaves. Some source candidates remain potentially recoverable; compiling pinned source, deeper CFG comparison, verified external mappings or bounded runtime fixtures would be new work. We stop after exhausting this useful finite directly grounded shortlist, without claiming no further recovery is possible.

The JAR declares 6,451 methods / 3,204 fields (main 4,665 / 1,751), including 957 constructors,208 class initializers,936 synthetic methods,17 native methods and 207 abstract methods; these categories overlap. Subtracting mapped rows is not a meaningful count of required research tasks. Semantic class roles and member coverage have no known finite target equal to original-name recovery.

## Evidence and rerun

Exact Modrinth artifact `Zqooxsd2`: SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, SHA-1 `151ac7b24da8beeca1a20864565743cfd77af286`, 63,269,843 bytes. Keep the JAR outside the repository. Official source is pinned to `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`; OpenYSM `a515d44686af77155a311b2a592327ca5d45a658` is comparative only. Prior Chinese compatibility evidence remains provenance/fixture hints. Global `SOURCE_ARTIFACT_DIVERGENCE` remains; item-level mismatch flags are not inferred from the global caveat.

Fresh scanner: 604 contracts, zero failures. Eleven prior/new dossier audits: 3,772 checks, zero failures. Ten concrete corrupt-evidence controls all reject. 185 source-file SHA-256 records verified. IDs and full kind/owner/member/descriptor targets are unique. Foundation rebuild covers 955 classes, 3,618 undirected edges, 3,823 directed refs, 19 components and 294 seeds. [SEMANTIC-VERIFICATION-2026-10-05.json](SEMANTIC-VERIFICATION-2026-10-05.json) records results.

From this directory, with an external exact artifact path:

```bash
YSM_JAR=/absolute/path/to/ysm-2.6.5-forge+mc1.20.1-release.jar
python tools/scan_ysm_265.py --jar "$YSM_JAR" --map OBFUSCATION-MAP-2026-10-05.json --out /tmp/ysm-scan.json
python tools/audit_seed_recovery_ysm_265.py --jar "$YSM_JAR" --evidence MOLANG-LOOP-EVIDENCE-2026-10-05.json --out /tmp/ysm-loop-audit.json
python tools/check_campaign_negatives_ysm_265.py --jar "$YSM_JAR" --out /tmp/ysm-negative-audit.json
python tools/cluster_ysm_265.py --jar "$YSM_JAR" --map OBFUSCATION-MAP-2026-10-05.json --out /tmp/ysm-foundation.json
```

Repeat the same audit command for each evidence filename listed above and the three prior seed/evaluation/evaluator dossiers. The durable audit checks flags/full descriptors, order-independent declarations, selected typed/literal/constructor-registration relations, ordered instructions/references, handlers, encoded operands and BootstrapMethods. The negative harness needs no private helper. Source hashes/URLs are in [SOURCE-INVENTORY-2026-10-05.json](SOURCE-INVENTORY-2026-10-05.json).

No raw JAR, runtime native/protection/decryption execution or model authorization bypass is included. This milestone closes the finite campaign; a future explicitly scoped pass could build compilation/runtime fixtures for the unresolved Java candidates.

The 18 source-hint followup and singleton are audited by the same retained tool:

```bash
python tools/audit_seed_recovery_ysm_265.py --jar "$YSM_JAR" --evidence SOURCE-HINT-FOLLOWUP-EVIDENCE-2026-10-05.json --out /tmp/ysm-source-hint-audit.json
```

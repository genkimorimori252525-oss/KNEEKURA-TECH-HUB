# FerriteCore — scoped failure / repair

Scope: upstream `malte0811/FerriteCore`, 2023-07–2023-08, baked quad dedup + #129 only. No broad history coverage.

## FC-129

- Symptom (REPORTER): [Issue #129](https://github.com/malte0811/FerriteCore/issues/129): Minecraft 1.20.1 with FerriteCore, ModelGapFix, Chipped reportedly increased loading (roughly 23 s → 70 s in reporter's setup). This is **not** KNEEKURA's own benchmark.
- Countermeasure report: reporter reported setting `bakedQuadDeduplication=false` mitigated issue; not independently reproduced.
- Upstream actual repair [commit `2aa56a0def18...`](https://github.com/malte0811/FerriteCore/commit/2aa56a0def18a94574bc4c0f6e1aea00db1709a5) (2023-08-10): changes `BAKED_QUAD_CACHE` hash from `Arrays::hashCode` to `betterIntArrayHash` using MurmurHash3 per element. Equivalence remains `Arrays::equals`. Compared parent `5087367f63289248b778c183e53c7d6a303d675d` (pre-fix state, **not necessarily introducing commit**) and after source `Deduplicator.java`.
- Root cause (AUTHOR_CLAIM + code-level INFERENCE): hash bucket collisions for similar packed quad arrays degrade dedup lookup throughput. Source comment explicitly references #129. Proof of which inputs collide in exact JAR or long-run performance still missing.
- Lesson: canonicalization saves memory **only when** collision/equality/retention costs remain bounded; implement hash-quality and reload tests.
- `reproduction`: **REPORTED only**. `fix_verification`: **NOT_RUN** in KNEEKURA. Upstream closed issue != runtime PASS.

Evidence locator: [before](https://github.com/malte0811/FerriteCore/blob/5087367f63289248b778c183e53c7d6a303d675d/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java); [after](https://github.com/malte0811/FerriteCore/blob/2aa56a0def18a94574bc4c0f6e1aea00db1709a5/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java).

Evidence raw API/captured bytes and CAS document IDs not minted. Machine-readable draft kept for review only, **NOT_IMPORTED** into history adapter.

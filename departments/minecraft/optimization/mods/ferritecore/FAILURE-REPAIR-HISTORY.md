# ferritecore — selected failure/repair history (2026-10-11)

This is a **bounded, source-backed case**, not a whole-history review and **NOT_RUNTIME_VERIFIED**. User's named exact 1.20.1 JAR is not held, release/source parity unknown.

**Window:** 2023 Jul-Aug model deduplication issue #129 and fix 2aa56a0 (Minecraft 1.20.1 report; 1.20.0 source candidate).  
**Source reference head:** `e47bcbbde5b83805f927bad82bcc2b323e7169b8`, track ANCHOR_ADJACENT.  
**Issue:** [#129](https://github.com/malte0811/FerriteCore/issues/129).  
**Verified fix commit:** [`2aa56a0def18a94574bc4c0f6e1aea00db1709a5`](https://github.com/malte0811/FerriteCore/commit/2aa56a0def18a94574bc4c0f6e1aea00db1709a5) (parent `5087367f63289248b778c183e53c7d6a303d675d`).  
**Compared file:** [pre-fix](https://github.com/malte0811/FerriteCore/blob/5087367f63289248b778c183e53c7d6a303d675d/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java) and [post-fix](https://github.com/malte0811/FerriteCore/blob/2aa56a0def18a94574bc4c0f6e1aea00db1709a5/Common/src/main/java/malte0811/ferritecore/impl/Deduplicator.java); actual source read in both revisions, change diff read.

| Facet | Statement | Basis |
|---|---|---|
| Symptom | Reporter observed ModelGapFix+Chipped load time roughly 23s without FerriteCore versus 70s with it. | USER/MAINTAINER REPORT |
| Trigger | ModelGapFix+Chipped+FerriteCore in user Minecraft 1.20.1 environment | USER REPORT / HISTORY |
| Root-cause interpretation | Maintainer identified weak hash collisions among similar baked quad vertex arrays leading to many array comparisons | AUTHOR_CLAIM (no independent reproduction) |
| Actual repair | Replace Arrays.hashCode(int[]) with betterIntArrayHash combining per-int MurmurHash3, retain Arrays.equals exact key equality | DIRECT_OBSERVATION of source diff |
| Portable lesson | Hash collision distributions matter for content-addressed resource reuse; profile cache construction and key similarity, not just heap savings. | SCOPED INFERENCE |
| Runtime reproduction | **NOT_RUN** | no authenticated LAB result |
| Fixed-version smoke / A-B perf | **NOT_RUN** | no paired benchmark |

Do not confuse a **closed Issue, code patch or author's “fixed” message** with a modern Forge 1.20.1 runtime acceptance PASS. Later regressions and source-JAR parity not exhaustively checked.

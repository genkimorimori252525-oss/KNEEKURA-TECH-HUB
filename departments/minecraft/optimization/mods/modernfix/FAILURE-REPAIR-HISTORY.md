# modernfix — selected failure/repair history (2026-10-11)

This is a **bounded, source-backed case**, not a whole-history review and **NOT_RUNTIME_VERIFIED**. User's named exact 1.20.1 JAR is not held, release/source parity unknown.

**Window:** 2023 Dec to 2024 Jan dynamic DFU vs Litematica issue #332 and fix ae8cfb.  
**Source reference head:** `cf04b47d10ac5c6a748b177ce0348a3b1e4a9871`, track ANCHOR_CANDIDATE.  
**Issue:** [#332](https://github.com/embeddedt/ModernFix/issues/332).  
**Verified fix commit:** [`ae8cfbaa3d880a20b70a418f4ae276312fa30981`](https://github.com/embeddedt/ModernFix/commit/ae8cfbaa3d880a20b70a418f4ae276312fa30981) (parent `675c58a437f68b42f9daa7bfc4b143d0003f7dba`).  
**Compared file:** [pre-fix](https://github.com/embeddedt/ModernFix/blob/675c58a437f68b42f9daa7bfc4b143d0003f7dba/common/src/main/java/org/embeddedt/modernfix/core/config/ModernFixEarlyConfig.java) and [post-fix](https://github.com/embeddedt/ModernFix/blob/ae8cfbaa3d880a20b70a418f4ae276312fa30981/common/src/main/java/org/embeddedt/modernfix/core/config/ModernFixEarlyConfig.java); actual source read in both revisions, change diff read.

| Facet | Statement | Basis |
|---|---|---|
| Symptom | Reporter found an empty Litematica schematic while dynamic DFU optimization was enabled | USER/MAINTAINER REPORT |
| Trigger | Litematica + ModernFix dynamic_dfu enabled | USER REPORT / HISTORY |
| Root-cause interpretation | Maintainer says lazy DFU startup skipped an initialization side effect expected by Litematica Mixin | AUTHOR_CLAIM (no independent reproduction) |
| Actual repair | Insert disableIfModPresent for mixin.perf.dynamic_dfu when mod ID litematica is installed | DIRECT_OBSERVATION of source diff |
| Portable lesson | Lazy initialization can change third-party class transform side effects; conditionally gate optimization instead of making a risky loader-wide assumption. | SCOPED INFERENCE |
| Runtime reproduction | **NOT_RUN** | no authenticated LAB result |
| Fixed-version smoke / A-B perf | **NOT_RUN** | no paired benchmark |

Do not confuse a **closed Issue, code patch or author's “fixed” message** with a modern Forge 1.20.1 runtime acceptance PASS. Later regressions and source-JAR parity not exhaustively checked.

# servercore — selected failure/repair history (2026-10-11)

This is a **bounded, source-backed case**, not a whole-history review and **NOT_RUNTIME_VERIFIED**. User's named exact 1.20.1 JAR is not held, release/source parity unknown.

**Window:** 2024 May activation tick immunities historical repair and 2024 Oct Forge 1.21.1 reported farm regression.  
**Source reference head:** `d1d0a02d39d0739441419e3a20f46fbc88d98ec5`, track ANCHOR.  
**Issue:** [#118](https://github.com/Wesley1808/ServerCore/issues/118).  
**Verified fix commit:** [`2238660d4be5e56336e7f9a890cb7f42138eaf82`](https://github.com/Wesley1808/ServerCore/commit/2238660d4be5e56336e7f9a890cb7f42138eaf82) (parent `845a152d694b51484a9ea39b82eee8826db790eb`).  
**Compared file:** [pre-fix](https://github.com/Wesley1808/ServerCore/blob/845a152d694b51484a9ea39b82eee8826db790eb/common/src/main/java/me/wesley1808/servercore/common/activation_range/ActivationRange.java) and [post-fix](https://github.com/Wesley1808/ServerCore/blob/2238660d4be5e56336e7f9a890cb7f42138eaf82/common/src/main/java/me/wesley1808/servercore/common/activation_range/ActivationRange.java); actual source read in both revisions, change diff read.

| Facet | Statement | Basis |
|---|---|---|
| Symptom | Author reports entities could remain inactive despite tick immunity; reporter in separate 1.21.1 issue observed altered iron farm efficiency | USER/MAINTAINER REPORT |
| Trigger | Stale activatedTick across shouldTick early-return, and separately 1.21.1 exclusion config needing chunk reload | USER REPORT / HISTORY |
| Root-cause interpretation | Author identified missing activatedTick update on an early return as a failure to re-check entity immunities immediately | AUTHOR_CLAIM (no independent reproduction) |
| Actual repair | Update activated tick before returning when shouldTick allows immediate work | DIRECT_OBSERVATION of source diff |
| Portable lesson | Scheduling optimization must track state transitions and exemptions; inactive ticks may break world mechanics and farm logic. | SCOPED INFERENCE |
| Runtime reproduction | **NOT_RUN** | no authenticated LAB result |
| Fixed-version smoke / A-B perf | **NOT_RUN** | no paired benchmark |

Do not confuse a **closed Issue, code patch or author's “fixed” message** with a modern Forge 1.20.1 runtime acceptance PASS. Later regressions and source-JAR parity not exhaustively checked.

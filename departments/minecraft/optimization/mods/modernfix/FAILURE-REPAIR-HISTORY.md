# ModernFix — scoped failure / repair

Scope: `embeddedt/ModernFix` issue #332 and specific `dynamic_dfu` gating change (2023-12–2024-01). Other 1.20 Mixins and histories NOT_ANALYZED.

## MF-332 — lazy DFU broke mod-dependent class initialization

- [Issue #332](https://github.com/embeddedt/ModernFix/issues/332): reported Litematica `.schematic` loads became empty with ModernFix dynamic DFU; turning off dynamic DFU avoided the problem.
- Maintainer's diagnosis: Litematica injects into vanilla flattening class, which loads as side effect of eager DFU startup. Lazy initialization prevents class from being loaded before Litematica's conversion path. This is a maintainer-reasoned causal report; exact KNEEKURA reproduction NOT_RUN.
- Actual [repair diff `ae8cfbaa3d880a20b70a418f4ae276312fa30981`](https://github.com/embeddedt/ModernFix/commit/ae8cfbaa3d880a20b70a418f4ae276312fa30981), parent `675c58a437f68b42f9daa7bfc4b143d0003f7dba`, adds the module conflict guard `disableIfModPresent("mixin.perf.dynamic_dfu", "litematica")`.
- Selected `1.20` source HEAD `cf04b47d10ac5c6a748b177ce0348a3b1e4a9871` **still contains that gate** (line 312 of `ModernFixEarlyConfig.java` at inspected revision).
- No source-observed alteration of Litematica itself. No runtime integration test or actual observed gains.
- Lesson: laziness changes **load side effects/order**, not just CPU time. Detect affected mod IDs and preserve fallback eager path.
- Reproduction: REPORTED. Fix verification: NOT_RUN. Scope distinct from unrelated ModernFix issues.

Before/after captures not CAS-imported; Git locator/diff inspected and qualified; JSON remains research draft only.

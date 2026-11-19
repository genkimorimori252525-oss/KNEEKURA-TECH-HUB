# MemoryLeakFix — bounded issue/mixin history with track gates

**History scope:** 2023 Forge 1.18.2 Saturn conflict #115, metadata #136, source revision `988f54c14db0d86e13dd5dcce284178b2278e581` with per-version Mixins; no verified exact 1.20.1 runtime cases.

## MLF-115 — Saturn overlapping transformation (NOT 1.20.1)

[Issue #115](https://github.com/FxMorin/MemoryLeakFix/issues/115) (2023-05-03) reports **Forge 1.18.2** fails to launch with both mods after Saturn update. Maintainer comments MemoryLeakFix implements same functions and more *for that setup*. This is source-maintainer opinion/report; an actual corresponding Mixin edit/fix commit is **NOT traced**. Cannot say Saturn `saturn-mc1.20.1-0.1.3.jar` is proven incompatible or redundant.

**Reusable lesson:** two memory-fix mods can patch the same singleton/cache constructor and collide; compare (Mixin target + method + loader mappings + enabled config + versions) before combining. No KNEEKURA recreation.

## MLF-136 — distribution metadata != code compatibility

[Issue #136](https://github.com/FxMorin/MemoryLeakFix/issues/136) (2023-07) says distribution listings only included MC 1.20, not 1.20.1, hindering launcher updates. Reporter comments metadata handled around 1.1.2. This is metadata/pack manager issue and cannot prove active Mixin or performance under all Forge 1.20.1 versions; exact binary audit pending.

## Code-level chronology / explicitly not an active ANCHOR fix

Source `Brain_clearMemoriesMixin` guarded `maxVersion 1.19.3`, comment Mojang fixed bug in 1.19.4; Drowned navigation fix only 1.16.3–1.16.5, TagKey strong interner fix only 1.18.2. These are **historic known scope** and not failure/repair cases for 1.20.1. No specific author fix commit linked to current 1.1.5 branch; report historical behavior but don't invent chain.

Total scoped cases: 2 reports and source guards, no inspected repair diff, no imported CAS history, no profiler/runtime tests.

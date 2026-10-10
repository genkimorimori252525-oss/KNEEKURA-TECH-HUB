# BadOptimizations — bounded repair histories

Scope: `imthosea/BadOptimizations`, 2024–2026, lightmap/sky cache invalidation and mod interoperability. Reports and code fixes pinned to versioned source, no benchmark/reproduction.

## BO-76 — Polytone resource pack stale lightmap (2024)

[Issue #76](https://github.com/imthosea/BadOptimizations/issues/76) user reports lightmap isn't refreshed after toggling custom Polytone resourcepacks when cache enabled. [Fix commit `dd8c2c1dc793...`](https://github.com/imthosea/BadOptimizations/commit/dd8c2c1dc793a11c3c2e10e453a96001654b9023), parent `135ed97319dec9d669a85b870fcd9c4ce1cbdb54`, directly adds Polytone mod-ID opt-out for **skyColor and lightmap** caching. The selected `1.20.1` source keeps `polytone` in built-in incompatibilities. Reported symptom and repaired policy supported, actual fix runtime NOT_RUN.

## BO-84 — Darkness pulsation stuck (1.20.1)

[Issue #84](https://github.com/imthosea/BadOptimizations/issues/84) user reports darkness effect stays dim instead of pulsing on Minecraft **1.20.1**. [Commit `e6085b5815...`](https://github.com/imthosea/BadOptimizations/commit/e6085b58154adb90ca99db99741997e74ef27cd6), parent `9f6f40402f58ecb8ae3f49979661620217cff6be`, directly adds special dirty check for active `DARKNESS` (plus helper restructure). Source `MixinLightTexture` at `f1540411...` still contains this check. No direct engine/render replay.

## BO-109 / BO-126 — extra risk leads, not proven 1.20.1 cause

[#109](https://github.com/imthosea/BadOptimizations/issues/109) argues third-party night vision strength can change without the potion's presence changing; source `CacheHooks` offers extra dirty callbacks, but a specific fix commit for #109 was NOT traced and source 1.20.1 still uses Boolean presence for night vision. Treat as incompatibility hypothesis. [#126](https://github.com/imthosea/BadOptimizations/issues/126) is explicitly Minecraft 1.21.1 **NeoForge** lightmap-stall report, not evidence target Forge 1.20.1 does same.

Core lesson: cache keys, dirty predicates, mod-ID exclusions, user settings, resource pack reload, and actively dynamic shaders/effects form one correctness contract. Performance NOT_RUN; CAS history import NOT_DONE.

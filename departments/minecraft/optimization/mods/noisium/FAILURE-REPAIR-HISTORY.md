# Noisium v2.3.0 — historical issue → repair evidence

History window: 2023–2024 selected #3, #10, #16, #31 and v2.0.2 to v2.3.0 changelog. ANCHOR Minecraft 1.20.1 Forge **source commit `8cf451809eca7cfae1dd839edad96fc9092c4ef8`**, no user JAR bytecode acquired.

## N-10 — Lily/Lithium/Canary-Radium block-section invariant

[Issue #10](https://github.com/Steveplays28/noisium/issues/10) (2023-12) reporter saw fish/squid fail to detect water in chunk sections with Noisium+Lithium, even as fluid visuals existed. Maintainer recognized direct palette writes skip the Lithium blockstate tracking Mixin. [Commit `a5aa5eac09647f93e0d3f32c66839bbdb0ff00f4`](https://github.com/Steveplays28/noisium/commit/a5aa5eac09647f93e0d3f32c66839bbdb0ff00f4) (2024-04-08), parent `36ab391a6e87a487ee474a33fe2e32de9669583d`:
- Before: one generic source hook; after: Mixin plugin chooses standard or compatible case based on loaded `lithium/canary/radium`.
- Added `compat.lithium.LithiumNoiseChunkGeneratorMixin`, recomputes section counts when unlocking after noise generation using `calculateCounts()`.
- Author [said released a fix in 2.0.2](https://github.com/Steveplays28/noisium/issues/10#issuecomment-2054134708); exact 2.3 source contains the compatibility implementation. **No independent GameTest/FPS**, no validation for arbitrary Canary/Radium builds.

Root is evidenced by source bypass and correction; precise original server stack not acquired. Lesson: a specialized fast-path must reproduce every third-party index/counter invariant, or select compatibility fallback.

## N-3 — rare missing sections in historical v1.0.0

[Issue #3](https://github.com/Steveplays28/noisium/issues/3), historical **1.0.0-era** user report rare missing chunk sections, reload fixes visual result. Maintainer comment “fixed in Noisium v1.0.1.” Exact release source before/after diff **not yet inspected**. Do not attribute this symptom or fix to v2.3.0 binary.

## N-16 — invisible water/lava on Fabric, multi-mod pack

[Issue #16](https://github.com/Steveplays28/noisium/issues/16) (2024), Fabric/C2ME/Lithium/ModernFix/Sodium and more. Some water/lava invisible until player right-click; replies suggest different possible causes (#10 tracking). No direct 2.3.0 Forge repair diff or reproduction. Root status UNKNOWN. Don't call Noisium the proven cause.

## N-31 — Biospherical Expansion no overlap on established 1.20.1 Forge

[Issue #31](https://github.com/Steveplays28/noisium/issues/31) report conflicting `@Overwrite` and generation feature-order cycles with Biospherical Expansion. `v2.3.0` CHANGELOG (2024-08-21) lists compatibility ban for **Fabric and NeoForge 1.21+**, so explicit Minecraft/loader scope matters.

**Knowledge status**: PARTIAL selected source/Issues, full upstream history and exact release hash unavailable; runtime tests NOT_RUN; machine-readable JSON research draft not history-adapter import ready without source CAS document IDs.

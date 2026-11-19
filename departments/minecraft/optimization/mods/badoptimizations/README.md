# BadOptimizations — guarded client tick/render-state caches

**Source:** [`imthosea/BadOptimizations@f1540411b21e8458d6d143d00f53743e7a9bc893`](https://github.com/imthosea/BadOptimizations/tree/f1540411b21e8458d6d143d00f53743e7a9bc893), branch `1.20.1`, **65 blobs / 43 Java** source path inventory `truncated=false`. In inspected `gradle.properties`: **mod 2.4.1, Minecraft 1.20.1, Forge 47.2.0**, Java 17. This matches version identifiers in user's `BadOptimizations-2.4.1-1.20.1.jar` name, **but binary SHA and source parity are still unverified**. Source [MIT](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/LICENSE); current FRONTIER [26.2 `5de4a3ad...`](https://github.com/imthosea/BadOptimizations/tree/5de4a3ad4299909178d8995dc0bc80626be48d44) discovered, not fully compared.

**Categories:** `TICK_SIMULATION`, `CACHE_DATA_STRUCTURE`, `RENDERING_GPU`, `MIXIN_BYTECODE`. Source evidence direct for selected `ClientLevel`, `LightTexture`, shader/render cache and plugin guards; runtime/benchmarks NOT_RUN.

## BO-01 — cancel redundant lightmap texture generation/upload

[`MixinLightTexture.tick`](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/mixin/tick/MixinLightTexture.java) intercepts lightmap tick and **cancels** it when cached `CommonColorFactors` and `bo$isDirty` both indicate no relevant change. Dirty conditions include:
- time delta ≥ configured `lightmapTimeForUpdate` (default source `80`);
- underwater fading, night vision appearance/disappearance/expiry, **Darkness active**, Conduit Power toggles;
- dimension effect, sky darkness, gamma slider and **third-party `CacheHooks.invokeLightmap`**.
- `ConfigOptimization.effectiveValue` depends on user setting and discovered incompatibility list; `ConfigLoadContext` default optimization setting true until disabled.

**Baseline:** lightmap computation and GPU texture upload repeatedly even when parameters unchanged. **Fast path** skips work; **fallback** when any invalidator fires is original `LightTexture.tick`. **Risks:** missed dynamic night vision strength, custom gamma/shader, resource reload, weather/daytime changes and changed dimension state; an inexact dirty predicate can freeze brightness.

## BO-02 — sky color when neighboring biomes uniform

[`MixinClientWorld.getSkyColor`](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/mixin/tick/MixinClientWorld.java) tests biome color around shifted camera samples. When varied, it falls through to vanilla interpolation/sampling; otherwise it reuses a cached `Vec3` or computes color from one biome and weather/lighting factors. `skyColorTimeForUpdate` source default `3`. CacheHooks can force invalidation.

**Risk:** sudden sky color boundary, custom biome color callbacks, gamma/dimension mods and incorrectly reused value. Repeated results need image/color tolerance test.

## BO-03 — smaller redundant client work and collision with other mods

[`MixinWorldRenderer`](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/mixin/MixinWorldRenderer.java) caches current sky angle in local shared reference across `LevelRenderer.renderSky` calls; `MixinParticleManager` returns early if particle map is **empty**. These are separate from Particle Core's async ticking and camera-distance cull.

**Compatibility barrier:** [`ModIncompatibilities`](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/config/ModIncompatibilities.java) registers disable-by-mod rules. Very relevant to Techhub: **`twilightforest`** disables `enable_entity_renderer_caching`; **`polytone`** disables `enable_lightmap_caching` and `enable_sky_color_caching`; `camera_lock_on` disables one FOV opt; other registered IDs / external mod-provided custom rules considered. [`CacheHooks`](https://github.com/imthosea/BadOptimizations/blob/f1540411b21e8458d6d143d00f53743e7a9bc893/common/src/main/java/me/thosea/badoptimizations/hook/CacheHooks.java) accepts extra BooleanSupplier hooks so a mod can request color refresh without blanket disabling caching.

**Warning**: `ignore_mod_incompatibilities` / `ignore_mod_cache_hooks` can bypass safety guards. `ConfigOptimization.userValue` and `effectiveValue` are separate. A flag's presence is not evidence that a Mixin applies in every loader/order/installed mod combination; plugin guards require source/JAR verification.

## Real upstream issues and repairs

- [#76](https://github.com/imthosea/BadOptimizations/issues/76): Polytone custom lightmap did not update on resource pack reload. [Repair diff `dd8c2c1d...`](https://github.com/imthosea/BadOptimizations/commit/dd8c2c1dc793a11c3c2e10e453a96001654b9023) adds **Polytone exclusion** for lightmap/skycolor. In selected 2.4.1 source these guards exist.
- [#84](https://github.com/imthosea/BadOptimizations/issues/84): 1.20.1 Darkness visual pulsing broken. [Repair diff `e6085b58...`](https://github.com/imthosea/BadOptimizations/commit/e6085b58154adb90ca99db99741997e74ef27cd6) changed dirty-predicate ordering and treats active Darkness as a reason to recompute, visible in selected source.
- [#109](https://github.com/imthosea/BadOptimizations/issues/109): later mod author discusses varying Gamma Utils night vision intensity; selected 2.4.1 source tracks night-vision presence but **not full strength** in cached state. Hooks exist to add dynamic invalidation; **no direct issue-linked fix diff verified** in this investigation.
- [#126](https://github.com/imthosea/BadOptimizations/issues/126) source of sky/lightmap stuck report is **1.21.1 NeoForge** 2.4.1, not Forge 1.20.1.

## Performance vs correctness

No own measured FPS/CPU or GPU upload results. Authors' dramatic FPS screenshot is **author-only and different hardware/workload**, not TechHub evidence. Test Minecraft 1.20.1 Forge resource reload/Polytone/TwilightForest/Gamma Utils/night vision/darkness transitions; compare pixel sky, brightness across day-night, animations, near biome boundaries; render frametime median/p95/p99, separate disabled/individual toggles.

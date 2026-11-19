# MemoryLeakFix 1.1.5 — selectively version-gated leak fixes

Date: 2026-10-11. Owner filename `memoryleakfix-forge-1.17+-1.1.5.jar`, actual user JAR bytes **NOT_ACQUIRED**, no SHA-256, no source↔JAR parity/Forge runtime. Git repository [`FxMorin/MemoryLeakFix@988f54c14db0d86e13dd5dcce284178b2278e581`](https://github.com/FxMorin/MemoryLeakFix/tree/988f54c14db0d86e13dd5dcce284178b2278e581), `dev` branch pinned, Git tree `6659f786fb6105dcf75fd154fdac3ae332c5ec97`, **57 blobs / 28 Java source paths**, complete recursive path inventory but **selected bodies read**, not full archive. Archived repo. Selected source `gradle.properties`: version **1.1.5**, development **MC 1.20.4 Forge 49.0.14**, Architectury Forge+Fabric. Treat as **ANCHOR-adjacent / COMPARATIVE**, not evidence of exact 1.20.1 Forge build. Main `LICENSE` is **LGPL-2.1**, README also asks not to merge into other clients/mods without author permission (license compatibility/legal reuse needs independent check).

Categories `MEMORY`, `CACHE_DATA_STRUCTURE`, `CLIENT_RENDERING`, `MIXIN_BYTECODE`; static code evidence, performance `PERFORMANCE_NOT_VERIFIED`.

## MLF-01 — exact Minecraft-version gating is essential

[`MemoryLeakFixMixinConfigPlugin.shouldApplyMixin`](https://github.com/FxMorin/MemoryLeakFix/blob/988f54c14db0d86e13dd5dcce284178b2278e581/common/src/main/java/ca/fxco/memoryleakfix/config/MemoryLeakFixMixinConfigPlugin.java) reads per-Mixin `@MinecraftRequirement` and suppresses unmatched versions. Contains mapping and MixinExtras adaptation. Not every file under `mixin/` will be loaded for MC 1.20.1.

**Examples of code that MUST NOT be counted as active 1.20.1 fixes:**
- `entityMemoriesLeak/Brain_clearMemoriesMixin` / `LivingEntity_clearMemoriesMixin`: **`maxVersion="1.19.3"`**. Its Brain reference cleanup was resolved by vanilla in 1.19.4 per code comment; not native 1.20.1 fix.
- `drownedNavigationLeak/Drowned_navigationMixin`: **min 1.16.3, max 1.16.5**, excluded 1.20.1.
- `tagKeyLeak/TagKey_internerMixin`: **only 1.18.2**, excluded 1.20.1.

These are genuinely useful **historical COMPATIBILITY examples** but cannot be claimed performance features of the user 1.20.1 instance. Also compare ModernFix and Saturn separately for overlap.

## MLF-02 — single static ThreadLocal biome temperature cache

[`Biome_threadLocalMixin`](https://github.com/FxMorin/MemoryLeakFix/blob/988f54c14db0d86e13dd5dcce284178b2278e581/common/src/main/java/ca/fxco/memoryleakfix/mixin/biomeTemperatureLeak/Biome_threadLocalMixin.java) has `@MinecraftRequirement(minVersion="1.14.4")`: candidate for 1.20.1 if exact Mixin target matches. Wraps `ThreadLocal.withInitial` in each Biome constructor and replaces per-Biome ThreadLocal map with a **static shared `ThreadLocal<Long2FloatLinkedOpenHashMap>`**, initialized lazily. This reduces per-biome cache duplication without sharing a single mutable map **across threads** (each thread still has own ThreadLocal map). Conceptual improvement in baseline allocations/memory, but special caveat: static thread local persists for class lifetime and can retain references on long-lived worker threads. Determine invalidation and correct temperature results when biome/dimension changes. No benchmark.

## MLF-03 — clear stale client target and free screenshot buffers on failure

[`Minecraft_targetClearMixin`](https://github.com/FxMorin/MemoryLeakFix/blob/988f54c14db0d86e13dd5dcce284178b2278e581/common/src/main/java/ca/fxco/memoryleakfix/mixin/targetEntityLeak/Minecraft_targetClearMixin.java) clears `Minecraft.crosshairPickEntity` and `hitResult` before client `runTick` to release stale object refs. This is a client-side reference lifecycle change; selected code has no `@MinecraftRequirement` and could apply 1.20.1 depending on mappings/injection. Risk: different client mods may depend on `hitResult` between ticks.

[`Minecraft_screenshotMixin`](https://github.com/FxMorin/MemoryLeakFix/blob/988f54c14db0d86e13dd5dcce284178b2278e581/common/src/main/java/ca/fxco/memoryleakfix/mixin/hugeScreenshotLeak/Minecraft_screenshotMixin.java) has min1.17 and adds `GlUtil.freeMemory` on huge screenshot **error return path**, preventing direct native memory buffer leak on failure. Check target descriptor and screenshots in exact 1.20.1 Forge before reuse; such Mixin does not imply ordinary screenshot path has leak.

[`TextureUtil_freeBufferMixin`](https://github.com/FxMorin/MemoryLeakFix/blob/988f54c14db0d86e13dd5dcce284178b2278e581/common/src/main/java/ca/fxco/memoryleakfix/mixin/readResourcesLeak/TextureUtil_freeBufferMixin.java) catches exceptions while loading resource textures, `MemoryUtil.memFree(buffer)`, but is **NOT LISTED in the inspected `memoryleakfix.mixins.json`**; may be supplied through separate version 1.16 config. Its class has `@Pseudo`, older method remapping. Inventory only, **do not assert loaded as active for 1.20.1**.

## Failure / compatibility evidence

[Issue #115](https://github.com/FxMorin/MemoryLeakFix/issues/115), 2023 Forge **1.18.2** report: MemoryLeakFix and Saturn both modify shared target causing launch failure. Maintainer comment says MemoryLeakFix covers Saturn's fixes in that environment, but **not a verified statement about Saturn 0.1.3 + MemoryLeakFix 1.1.5 on Forge 1.20.1**. [Issue #136](https://github.com/FxMorin/MemoryLeakFix/issues/136) demonstrates distinction between actual runtime compatibility and platform release metadata; users requested official Forge 1.20.1 marking, commenter says addressed in v1.1.2. Need exact JAR metadata. More in [history](FAILURE-REPAIR-HISTORY.md).

## Remaining proof

Read full source and Mixins/dependency closure for exact 1.1.5, identify active vs excluded features after loaded bytecode, compare 1.20.1 Forge mappings and client/screenshot hooks, memory heap retained before/after and multiple world reloads. No runtime loaded or PASS.

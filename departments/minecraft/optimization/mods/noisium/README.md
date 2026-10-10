# Noisium 2.3.0 — direct noise-palette writes, counter invariants and Lithium-fork interoperability

Date 2026-10-11. Target owner basename `noisium-forge-2.3.0+mc1.20-1.20.1.jar`. **Exact version snapshot:** GitHub [`Steveplays28/noisium@8cf451809eca7cfae1dd839edad96fc9092c4ef8`](https://github.com/Steveplays28/noisium/tree/8cf451809eca7cfae1dd839edad96fc9092c4ef8), commit 2024-08-21 **"Bump version number to v2.3.0"**. Git tree **`903a3ed58981d0ccc9f481c1159cdb766ac74e67`**, **57 blobs / 13 Java source paths**, no truncation; selected source bodies read, full-tree *bytes* NOT_ACQUIRED. Source `gradle.properties`: mod **2.3.0**, Minecraft **1.20.1**, supported `>=1.20 <=1.20.1`, Java 17, fabric+forge modules, development `neoforge_version=47.1.100`; Forge metadata also exists. Source 2.3.0 identity is matched to *requested version label* but owner JAR SHA/class/Mixin parity **NOT VERIFIED**.

**Important historical pitfall:** the branch `1.20-1.20.1` now points at mod **2.7.0** ([commit `c640041c`](https://github.com/Steveplays28/noisium/commit/c640041c8c932b36753c0ccf43902ac8b0bd252d)), **not** the user's 2.3.0; don't infer its later fixes. Source license [LGPLv3](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/LICENSE). `FRONTIER` Minecraft 1.21+ branches exist but their current APIs are separate `NOT_ANALYZED`.

## N-01 — skip normal ChunkSection.setBlockState in virgin noise-filled sections

At [`NoiseChunkGeneratorMixin.java`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/NoiseChunkGeneratorMixin.java) the Mixin redirects only the `NoiseChunkGenerator.populateNoise` call to `ChunkSection.setBlockState(...,Z)`. It obtains the block's ID from the palette then **directly writes palette bit-storage at section index** using `storage().set(index,id)`. Before write it manually increments **nonEmptyBlockCount**, **nonEmptyFluidCount** (if nonempty fluid) and **randomTickableBlockCount** (if random ticks), compensating for counters the bypassed vanilla setter updates.

**Baseline**: vanilla `setBlockState` handles palette lookup, locking/bookkeeping, old-state counter decrement and a slow generic state transition. **Fast path**: during noise generation, new block slots presumed air, avoid full setter. **Guard** is *callsite* (noise generation only); there is no visible runtime check that overwritten position truly was air. Thus direct write is **not safe as a generic terrain mutation primitive** (especially reversible siege, explosions or existing fluids). Side effect risk: lighting/heightmap, modded `ChunkSection.setBlockState` Mixins, tracking counters, race/locks. Benchmark `PERFORMANCE_NOT_VERIFIED`, not an independent measured speedup.

## N-02 — restore Lithium/Radium/Canary tracking invariants

[Issue #10](https://github.com/Steveplays28/noisium/issues/10) originally reported Lithium entities no longer detecting fluid in generated sections, because Lithium tracks per-section block flags via hooks in normal `setBlockState`, bypassed by direct write. **Actual fix diff** [`a5aa5eac09647f93e0d3f32c66839bbdb0ff00f4`](https://github.com/Steveplays28/noisium/commit/a5aa5eac09647f93e0d3f32c66839bbdb0ff00f4) (2024-04-08, parent `36ab391a6e87a487ee474a33fe2e32de9669583d`) adds a Mixin plugin selecting the compatible override and recalculates section counts with `calculateCounts()` after generation.

At exact v2.3.0 [`NoisiumMixinPlugin`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/NoisiumMixinPlugin.java) picks either regular `NoiseChunkGeneratorMixin` when none present, **or** [`compat.lithium.LithiumNoiseChunkGeneratorMixin`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/compat/lithium/LithiumNoiseChunkGeneratorMixin.java) when `lithium`, **`canary`**, or `radium` loaded. This alternate Mixin invokes `chunkSection.calculateCounts()` near section `unlock()`, restoring tracking class counters rather than just the three vanilla counters.

**Exact caution**: static compatibility selection from MOD IDs is source-backed but not proof any given Canary version's internal tracking hook is correctly restored. In some selected current source the compatibility Mixin targets a named method `method_38328`, requiring transformed bytecode signature and loader validation. No Forge 1.20.1 source-binary parity.

## N-03 — cache stable generation-shape coordinate conversion

[`GenerationShapeConfigMixin`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/GenerationShapeConfigMixin.java) calculates `horizontalCellBlockCount` and `verticalCellBlockCount` in constructor once using `BiomeCoords.toBlock`, then intercepts getter calls. Cache owner = individual GenerationShapeConfig immutable instance, two int values, lifetime until instance release, invalidation if sizes ever dynamically changed (not evidenced). Should produce exact same values as vanilla under normal immutable config.

## N-04 — biome traversal and sampler loop specialization

[`ChunkSectionMixin`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/ChunkSectionMixin.java) **overwrites** `populateBiomes`, loops 4³ biome cells Y→Z→X then writes via `swapUnsafe`. [`ChainedBlockSourceMixin`](https://github.com/Steveplays28/noisium/blob/8cf451809eca7cfae1dd839edad96fc9092c4ef8/common/src/main/java/io/github/steveplays28/noisium/mixin/ChainedBlockSourceMixin.java) replaces enhanced foreach with indexed loop, returning first nonnull block state; stable sampler iteration ordering is a critical correctness contract. Earlier 2.0.2 changelog credits fixing the **axis-order** direction; this `v2.3.0` source reflects corrected order. Overwrite still risks Mixin incompatibility.

## Bug/repair/limitations (separate reports vs code)

- [Issue #10](https://github.com/Steveplays28/noisium/issues/10) Lithium fluid detection; author explicitly traced bypassed `setBlockState`, source repair diff reviewed and includes Canary/Radium labels.
- [Issue #3](https://github.com/Steveplays28/noisium/issues/3) rare missing chunk sections in older 1.0.0 era, developer says fixed in 1.0.1; **no actual historical patch diff acquired**.
- [Issue #16](https://github.com/Steveplays28/noisium/issues/16) invisible lava/water in multi-mod Fabric setup; no verified 2.3.0 Forge reproduction or source repair.
- [Issue #31](https://github.com/Steveplays28/noisium/issues/31) and v2.3.0 changelog: Biospherical Expansion potential feature-order cycle crash; stated for **Fabric and NeoForge 1.21+**, not established as Forge 1.20.1.

See [history](FAILURE-REPAIR-HISTORY.md).

## Validation and adoption

Test vanilla vs v2.3.0 with same seed/biomes, 1/100/1000 chunk generation; compare blockstate palette, fluid flags, collision/fluid sensing by fish, random tick count, biome cell index, lighting, heightmaps, saved/reloaded chunk checksums, vanilla/Lithium/Canary/Radium separately. Measure chunks/s and MSPT p95/p99 with profiler; **0 runtime and benchmarks so far**. No vanilla semantic fidelity or percent speedup is independently proven. Do not copy direct palette writes into generic world edits.

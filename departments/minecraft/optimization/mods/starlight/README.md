# Starlight 1.1.2 — Forge light engine, SWMR nibble lifecycle and update scheduling

**2026-10-11 target** `starlight-1.1.2+forge.1cda73c.jar`. The **7-digit build SHA embedded in JAR name `1cda73c`** resolves to official source [`PaperMC/Starlight@1cda73ccfa016e35d7cf0ed848bc8786f5881740`](https://github.com/PaperMC/Starlight/tree/1cda73ccfa016e35d7cf0ed848bc8786f5881740). Source `gradle.properties` says **mod 1.1.2, Minecraft 1.20 development + Forge 46.0.14**, supported range `[1.20,1.21)`. Named distribution **1.20.1 Forge** is supported by [actual upstream Issue #191](https://github.com/PaperMC/Starlight/issues/191) with **exact JAR filename** and reported Forge47.1.3; so this is the best fixed **ANCHOR source candidate** (not 1.1.3 branch head). **No JAR downloaded or SHA256/bytecode comparison**.

Immutable **tree `80aa0b29f290636a1af8d77b6e014ac9261a95fb`, 46 blobs / 28 Java** source paths, recursion not truncated; selected bodies read, full source bytes/CAS not acquired. Historical `forge` current head `c562a3a...` declares **1.1.3 Minecraft1.20.2 Forge48**, **NOT** source for requested JAR. Source license **LGPL-3.0-only**.

## STARLIGHT-01 — fast propagation with per-Chunk light ownership

Source [`StarLightEngine`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/src/main/java/ca/spottedleaf/starlight/common/light/StarLightEngine.java), [`BlockStarLightEngine`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/src/main/java/ca/spottedleaf/starlight/common/light/BlockStarLightEngine.java) and [`SkyStarLightEngine`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/src/main/java/ca/spottedleaf/starlight/common/light/SkyStarLightEngine.java).

- **Baseline**: vanilla lighting engine repeatedly propagates block/sky light across positions and chunk edges.
- **Mechanism**: a shared breadth-first propagation strategy handles increases/decreases; block/sky-specific callers decide light sources. `StarLightEngine` caches a **5×5 chunk neighborhood** plus section/nibble arrays and mutable positions for each operation, populates against `LightChunkGetter` and rejects missing required loaded radius in selected `setupCaches`.
- **Correctness**: darkness/skylight/occlusion should be consistent with vanilla final light values; correctness also means no deadlocks/chunk-load side effects. Renderer lighting precision and light packet serialization require further facet work.
- **Cache**: per operation temporary sections/nibbles, `destroyCaches` nulls cached chunk references in finally, important to avoid leaked LevelChunks.
- **Owner**: `StarLightInterface` per level light provider with cached Block/Sky propagator instances. It is a **complete light engine rewrite**, NOT a small FPS tweak.
- **Complexity**: Code comments document packed direction and position queues and section-boundary behavior. End-to-end benchmark not run.

## STARLIGHT-02 — per-section SWMR NibbleArray (2,048 bytes per lighting section)

[`SWMRNibbleArray`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/src/main/java/ca/spottedleaf/starlight/common/light/SWMRNibbleArray.java) stores light values 0..15 packed two per byte: `16×16×16/2=2048` bytes. Tracks **null/uninitialised/initialised/hidden** state. Storage has writer-owned `storageUpdating` and `volatile storageVisible` for reader use, with a copy-on-write stage when modified, then `updateVisible()` publishes under synchronization. A `ThreadLocal<ArrayDeque<byte[]>>` pools temporary arrays.

**Cache contract**: key = chunk/light section + offset; value = nibble and visibility state; owner = LevelChunk / StarLightEngine operation; max 2,048 B per initialized section plus metadata; lifetime = chunk, with temporary per-propagator pooled buffers; invalidation via `updateVisible`, per-chunk lifecycle, unload; stale consequences = dark/light rendering bugs and mismatch on clients.

## STARLIGHT-03 — grouped changed blocks and asynchronous chunk task semantics

[`StarLightInterface.LightQueue`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/src/main/java/ca/spottedleaf/starlight/common/light/StarLightInterface.java) uses `Long2ObjectLinkedOpenHashMap<ChunkTasks>`, synchronizes queue insertion by chunk key and aggregates `Set<BlockPos> changedPositions` + changed sections and edge checks. `propagateChanges()` processes sky/block engines together, completes per-chunk CompletableFuture and releases engines in finally. Repeated changes within same chunk are grouped into a single task rather than independent unbounded light recalculations. Precise ordering/deadlock under Forge worker threads is a separate critical correctness test.

## Critical performance & version caveat

**Do not promote pre-1.20 “Starlight vastly outperforms vanilla” graphs to 1.20.1.** Author [`TECHNICAL_DETAILS.md`](https://github.com/PaperMC/Starlight/blob/1cda73ccfa016e35d7cf0ed848bc8786f5881740/TECHNICAL_DETAILS.md) begins with a **1.20 obsoletion notice**: Mojang 1.20 vanilla copied much of Starlight's innovations, making older comparisons invalid; 10k-chunk gen benchmark discarded for 1.20+ due vanilla COW light-map behavior. README says measured block-light operations on 1.20-rc1 were faster but **absolute durations unlikely to change client FPS**; reported results on Ryzen7950X are AUTHOR_MEASUREMENT, not Techhub benchmark. Starlight entire light engine integration and modded off-thread BlockEntity light queries carry compatibility risk.

## Exact user JAR crash report + live upstream diagnostic (not a repair)

[Starlight Issue #191](https://github.com/PaperMC/Starlight/issues/191) is *exact* `starlight-1.1.2+forge.1cda73c.jar` on Forge 47.1.3/MC1.20.1 with **Framed Blocks 9.0.3** and crash in light emission access. Maintainer closed as duplicate of **[Issue #197](https://github.com/PaperMC/Starlight/issues/197) still OPEN**; author states `IForgeBlockGetter#getExistingBlockEntity` missing off-thread check can invoke `getChunk()` and block waiting for main thread on worker while another thread waits for light, producing deadlock. [Issue #186](https://github.com/PaperMC/Starlight/issues/186) is same exact 1.1.2 Forge with Create elevator/windmill actions crash; no source-linked fix acquired. These are **upstream reports + maintainer diagnosis**, not a proven Starlight code fix. See [history](FAILURE-REPAIR-HISTORY.md).

## Future acceptance

Baseline vanilla 1.20.1 light engine vs exact Starlight 1.1.2 JAR: light levels at same coordinates, stage->chunk transitions and client packets, day/night/sea/cave, 10000 block placing/breaking patterns, chunk border + Height range, Create rotating machinery/Framed Blocks custom emission on worker, locked chunk-deadlock detector, shader render p95 and MSPT. Test combinations with Noisium direct palette writes: section count/light engine status must remain consistent. **No Forge runtime, correct source-binary class equality or benchmarks performed.**

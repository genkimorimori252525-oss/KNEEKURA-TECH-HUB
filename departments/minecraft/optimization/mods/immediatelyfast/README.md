# ImmediatelyFast — RenderLayer batching, state restoration and draw-order safety

2026-10-11 Phase 3A source study: `RaphiMC/ImmediatelyFast` immutable [`1.20@b66885773494bfad58c83a8eee7b2f41424d4d9b`](https://github.com/RaphiMC/ImmediatelyFast/tree/b66885773494bfad58c83a8eee7b2f41424d4d9b), recursive Git source path index **141 blobs / 92 Java files** (`truncated=false`), selected central sources read. Pinned `gradle.properties` says **Minecraft development 1.20.4**, `supported_minecraft_versions=1.20,1.20.1,1.20.2,1.20.3,1.20.4`, **mod 1.5.6-SNAPSHOT**. User JAR `ImmediatelyFast-Forge-1.5.5+1.20.4.jar` not acquired/hashed and source/JAR parity **UNVERIFIED**.

**Important verified distribution fact:** [official Modrinth 1.5.5 Forge release](https://modrinth.com/mod/immediatelyfast/version/1.5.5%2B1.20.4-forge) declares **Minecraft 1.20–1.20.4** Forge, including **1.20.1** despite `+1.20.4` filename. This proves **declared support**, not successful 1.20.1 modpack runtime. License [LGPL-3.0-or-later](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/LICENSE); no library/media copied.

**Categories**: `RENDERING_GPU`, `RESOURCE_DATA`, `CACHE_DATA_STRUCTURE`, `MIXIN_BYTECODE`. **PERFORMANCE_NOT_VERIFIED**.

## IF-RENDERLAYER-BATCH: accumulate intermediate GUI vertex buffers

Source: [`BatchingBuffers`](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/common/src/main/java/net/raphimc/immediatelyfast/feature/batching/BatchingBuffers.java), [`BatchableBufferSource`](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/common/src/main/java/net/raphimc/immediatelyfast/feature/core/BatchableBufferSource.java), [`BatchingRenderLayers`](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/common/src/main/java/net/raphimc/immediatelyfast/feature/batching/BatchingRenderLayers.java).

Baseline: regular immediate-mode GUI/overlay renders frequently switch layers/shader states and send buffer data in many small draw operations.

Mechanism: per-render phase `beginHudBatching` redirects fill, texture, text, item model and item overlay `VertexConsumerProvider` into retained `BatchingBuffer` instances. `endHudBatching` draws collected buffers and **restores `RenderSystemState`**. [`MixinInGameHud`](https://github.com/RaphiMC/ImmediatelyFast/blob/b66885773494bfad58c83a8eee7b2f41424d4d9b/common/src/main/java/net/raphimc/immediatelyfast/injection/mixins/hud_batching/MixinInGameHud.java) injects around scoreboard/crosshair/status/hotbar etc. `forceDrawBuffers` marks ordering barriers (e.g. hotbar texture before items).

Guards/fallback:
- `ImmediatelyFastConfig.hud_batching=true` by source default; `experimental_screen_batching=false`; `experimental_sign_text_buffering=false`.
- For incompatible/shared-vertex layers, `BatchableBufferSource.getBuffer` rejects illegal vertex sharing; a pool of fallback buffers permits uncommon layers rather than concatenating all into one invalid stream.
- `IrisCompat` changes map/data structures and extended vertex state when shader active; not proof of correctness for every shader mod.
- `BatchingRenderLayers.memoizeTemp` cache uses **expireAfterAccess(1 second)** for constructed render layers. Key is argument or argument pair, owner is respective function wrapper. Full lifetime of static `COLORED_TEXTURE` memoization differs from expiring wrappers; avoid universal “1s cache” claim.
- `SignTextCache` has 5s expiration + `clearCache` on resource reload, but **sign text buffering is experimental and disabled by default**. Do not count its impact in default benchmark.

## IF-LAYER-ORDER — batching changes semantics unless stable order maintained

Rendering order of special overlays matters because glint, text, depth test and transparency are not always commutative. `getLayerOrder` assigns special orders for text, villager overlays, glint/armor/textures, and mod-specific shims; can arrange fallback draws. `debug_only_use_last_usage_for_batch_ordering=false` source default; certain named layers `immediatelyfast:renderlast` opt in independently.

The code explicitly warns and closes a prior active batch if `beginHudBatching` called twice without matching end. That prevents stale persistent buffers but logs an error and is not a guarantee no frame state was corrupted.

**Upstream repair diffs verified**: [#181 / `3f7d86fb`](https://github.com/RaphiMC/ImmediatelyFast/commit/3f7d86fbdafb64fbb6e087e53bd3444bed4a717b) adds optional last-usage batch reordering for item glint, while [#287/#288 / `f9fbf5d83...`](https://github.com/RaphiMC/ImmediatelyFast/commit/f9fbf5d83d6bd2bd73f403f833c419fff26a7368) assigns text layer priority to preserve overlapping custom-font/title readability. Selected 1.20 source contains relevant ordering logic; **exact 1.5.5 release attribution not established**.

[Issue #129](https://github.com/RaphiMC/ImmediatelyFast/issues/129) is open user report on **1.20.1** HUD XP level obscured when ModernUI installed; reporter states `hud_batching=false` mitigates. **No verified repair**. Important because user cohort has UI MODs and ModernFix (different mod from ModernUI).

## Source portability

Current 1.20 source Mixin classes use Yarn namespace in development, `forge` loader module uses Forge metadata `minecraft=[1.20,1.20.4]`; direct 1.20.1 mapping ABI/embedded adapters still require released 1.5.5 artifact inspection. FRONTIER separate [`26.3@a756fbac...`](https://github.com/RaphiMC/ImmediatelyFast/tree/a756fbac991bc8aacc2400347f050392193ae51c), not reviewed for feature parity.

## Runtime acceptance still absent

Same GUI with overlapping fonts, custom HUDs, boss bars, glints, translucent enchant overlays; test GL shader combos, world unload/reload, resource reload, modded entity armor textures, FPS median/p95/p99 + draw calls/GPU frame time. **No run/binary measurements or complete 92-source-file code audit**.

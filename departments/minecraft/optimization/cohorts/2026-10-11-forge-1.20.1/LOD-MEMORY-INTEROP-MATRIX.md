# LOD and memory optimizer boundaries — Phase 4/5

**Date:** 2026-10-11. **Scope:** selected public source, **NO combined Forge 1.20.1 JARs or performance benchmark**.

| Interacting code | Shared stage or resource owner | What makes it risky | Acceptance experiments still NOT_RUN |
|---|---|---|---|
| [Distant Horizons 3.2.0b](../../mods/distant-horizons/README.md) + [GPU Tape 1.0.5.1 candidate](../../mods/gputape/README.md) | depth/color framebuffer and GL texture IDs | DH already destroys old depth/color on viewport resize; a generic deferred cleaner that queues same GL handles could cause stale IDs, double deletes or wrong render context. **GPU Tape 1.0.5.1 exact code UNKNOWN**; don't assert real conflict | track per-FBO generation, resize/shader toggle, count GL deletes, VRAM use |
| Distant Horizons + [BFRC](../../mods/brute-force-rendering-culling/README.md) | GPU depth attachments and render pass scheduling | DH renders LOD before vanilla solid layer and can compose fog/fade; BFRC derives hierarchy from main depth buffers. Wrong ordering might hide LOD or distant vanilla sections | same scene at viewpoint switches, BFRC async on/off, shader state, captured depth hierarchy and visible chunk pixels |
| DH + [Embeddium](../../mods/embeddium/README.md) | vanilla chunk renderer replacement and shadow/render pass | differing chunk near-field/far-field cutoff and GPU draw states; "declared compatible" and source hooks are no end-to-end versioned tests | chunk seam hole count, camera flythrough, shaders, two-world unload/reload |
| [AllTheLeaks](../../mods/alltheleaks/README.md) + [ModernFix](../../mods/modernfix/README.md) | ingredient interning and early boot mixin gates | ATL `IngredientDedupe` checks ModernFix feature, **off by default**, may impose ItemStack lock and static intern lifetime | per-recipe semantics across datapack reload, heap dominator graph, config and mod-ID gates |
| AllTheLeaks + Forge EventBus versions | ListenerList cache invalidation at server stopped | EventBus PR#65 in >=6.2.26 invalidates eagerly; *old workaround* may create new never-used arrays | compare verified EventBus 6.0.5 vs 6.2.33 with pre/post heap captures |
| [MemoryLeakFix](../../mods/memoryleakfix/README.md) + Saturn | Mixins manipulating caches/singletons | Old **1.18.2** crash report, not proof user 1.20.1 same. Source MLF branches dev 1.20.4, some feature gates older. | exact 1.20.1 JAR mixin classes, target descriptors and invalid injections, no global disabling without evidence |
| AllTheLeaks + [Twilight Forest](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/tree/main/departments/minecraft) | JEI Transformation Powder entity preview and Hydra render model | source ATL patch targets TF >=4.3.2508 + JEI >=15.8.2.24; JEI model references may retain old client world between disconnect/relog | 5 repeated TF/JEI world unloads, GPU/histogram heap retained, Hydra draw correctness |

## Distinguish four separate outcomes

1. **Average FPS** and client GPU time; often **not** changed by GC leak repairs until long sessions.
2. **Resident Java heap** after unload (weak reference reachability/GC/heapdump), not just current heap high watermark.
3. **VRAM/live GL handle count** and correct context cleanup; separate from Java `System.gc()`.
4. **LOD cache generation/storage cost** (CPU/SQL/disk), may increase work while enabling further visible terrain.

No additive FPS performance claims: use same world/driver/hardware, one-mod-difference A/B, and verify correctness before profiler metrics.

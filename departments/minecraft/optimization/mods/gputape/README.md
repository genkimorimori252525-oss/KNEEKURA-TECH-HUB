# GPUTape / GPUBooster — renderer resource lifetime and loader-provenance investigation

Date: 2026-10-11. Request: `GPUTape-1.18x-1.21x-1.0.5.1.jar` in a Forge 1.20.1 folder. **Binary NOT_UPLOADED; SHA-256 NOT_ACQUIRED; exact loader variant and code parity UNESTABLISHED.**

## The source-identification trap

The previously indexed [`StarmanMine142/GpuTape@e57f961776195894ed23687f9c143fd6942b9d58`](https://github.com/StarmanMine142/GpuTape/tree/e57f961776195894ed23687f9c143fd6942b9d58) has **17 blobs / 3 Java**, a **Fabric 1.20.2 version 1.0.0 project** (`gradle.properties`, `fabric.mod.json`). Its README advertises Forge/NeoForge but its build is Fabric Loom and its source code still points at old GpuTape types. **It is not proof of the named 1.0.5.1 Forge JAR** and the code snippets must not be blindly reused.

The related original developer's [`ITsMrToad/GPUBooster`](https://github.com/ITsMrToad/GPUBooster) retains a historical `GpuTape-1.18-1.21` branch and later renamed GPUBooster work. Pinned [`16bf18cee756ab47a760da9e2892f1ea02d015b0`](https://github.com/ITsMrToad/GPUBooster/tree/16bf18cee756ab47a760da9e2892f1ea02d015b0) is **1.21.1 Fabric / 1.1.0** source: 18 blobs / 5 Java files (Git tree complete path list, **selected bodies read**). This is **COMPARATIVE**, not ANCHOR parity. The source `fabric.mod.json` in the branch even refers to old entrypoint name `VideoTape`, while actual class is `GpuTape`; no runtime/build smoke, so do not declare its actual jar broken.

**Distribution:** [Modrinth 1.0.5.1-forge](https://modrinth.com/mod/gputape/version/1.0.5.1-forge) lists Forge 1.20.x supported, while [CurseForge file 6200071](https://www.curseforge.com/minecraft/mc-mods/gputape/files/6200071) says **"NeoForge only for 1.20.1"** despite labeling Forge+NeoForge. Preserve this conflict as `COMPATIBILITY_CLAIM_DISAGREEMENT`. Filename alone does not establish actual loader or successful Forge boot.

## GPU-RES-01 — deferred texture/FBO destruction (historical comparative concept)

The later [`GpuTape.java`](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/src/main/java/com/mr_toad/gpu_tape/client/GpuTape.java) registers a **client tick callback** that drains at most **20** queued `FramebufferFixer` objects per tick. It switches GL bindings off once, and releases texture IDs/deletes framebuffer IDs via [`FramebufferMixin`](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/src/main/java/com/mr_toad/gpu_tape/client/mixin/FramebufferMixin.java) `destroy/release`, not by a global `System.gc()` call.

- Baseline: opaque OpenGL FBO/color/depth texture resources risk persisting after owner lifetime if cleanup not run correctly.
- Guard: queued fixers only for framebuffer with valid IDs and Vulkan inactive. Versioned Vulkan implementation is separate [`GlFramebufferMixin`](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/src/main/java/com/mr_toad/gpu_tape/client/mixin/vulkan/GlFramebufferMixin.java).
- Fast path: defer GL deletions to render/client lifecycle, cap per-tick queue draining at 20.
- Cache/owner: `ConcurrentLinkedQueue<FramebufferFixer>` static mod singleton; each enqueued instance retains its original GPU handles until drained. Queue capacity is **unbounded** despite 20/tick drain; backlog/gpu memory and double-release need test.
- Correctness: GL calls must execute with correct OpenGL context and exactly once; invalid texture ID reuse/double deletes and JVM Cleaner lifecycle require actual bytecode/world-close evidence. Java `Cleaner.Cleanable` implementation alone does **not** prove a Cleaner registration exists.
- Resource lifecycle: world switches, video settings, framebuffer recreation and shaders must not free active FBOs or retain stale ones.
- Other named source surface: [`gb.mixins.json`](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/src/main/resources/gb.mixins.json) and [`gb_gl.mixins.json`](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/src/main/resources/gb_gl.mixins.json) are Fabric/1.21.1 era (JAVA_21), **not 1.20.1 Forge Mixin proof**.
- **Performance status:** `MECHANISM_ONLY`, `PERFORMANCE_NOT_VERIFIED` (memory leak fixes aim for stability; do not present as FPS boost).

The current product name **GPUBooster** advertises additional OpenGL 4.5 DSA, RBO, pooling and fast math, but this **1.1+ FRONTIER** functionality is not established in the requested **1.0.5.1** release. Distinguish product marketing from anchored code.

## Upstream incident / bounded history

[Issue #5](https://github.com/ITsMrToad/GPUBooster/issues/5) user reports **1.0.5 Forge 1.20.1 crash**; maintainer [responded "Fixed in 1.0.5.1"](https://github.com/ITsMrToad/GPUBooster/issues/5#issuecomment-2585551866), and Modrinth 1.0.5.1-forge lists an instant Mixin crash fix. **This is MAINTAINER_CLAIM + RELEASE_NOTE**, not verified source before/after patch, and no exact user binary/hash; issue closed, **no independent Forge runtime PASS**.

History detail: [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md).

## What remains

Retrieve exact requested user JAR, read `mods.toml` / fabric metadata + all class names/Mixins & digest; distinguish Fabric, Forge vs NeoForge, pin `1.0.5.1` source release snapshot if discoverable; compare with old 1.0.0 and later 1.1.0 changes, evaluate GL context and resource deletion tests. Only after that could GPUTape-specific technique be promoted for Forge 1.20.1. Source distribution license branch says [GPLv3](https://github.com/ITsMrToad/GPUBooster/blob/16bf18cee756ab47a760da9e2892f1ea02d015b0/LICENSE), respect derivative/code obligations.

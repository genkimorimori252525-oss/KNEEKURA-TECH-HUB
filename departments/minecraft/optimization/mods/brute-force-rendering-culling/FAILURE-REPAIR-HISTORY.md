# BFRC — bounded issue/repair history

Scope: GitHub RogoShum/BruteForceRenderingCulling, 2024, targeted `0.5.12` chunk-visibility glitch and older shader conflict. Queries: `occlusion`, `visible`, `shader`, `async`. Binary and runtime NOT_ACQUIRED / NOT_RUN. **No supported issue-linked actual repair diff was found inside this window**; do not label closed issue as fixed.

## BFRC-27: exact release 0.5.12, newly visible chunks remain invisible

[Issue #27](https://github.com/RogoShum/BruteForceRenderingCulling/issues/27), Minecraft 1.20.1 Forge and Fabric, **0.5.12** (user report). Rotating view rapidly or stepping from behind occluder can reveal chunks late, especially low frame limit. Reporter distinguishes:
- frustum-related symptom only when async rebuild enabled;
- GPU occlusion-related symptom regardless of async rebuild toggle, mitigated by switching off chunk culling.

Source comparison: `CullingMap` buffers/transfer delay, `ChunkCullingMap` and `CullingStateManager.shouldRenderChunk` contain stale-result vulnerability *hypotheses*. **No causal commit/reproducer confirming exact root cause**. Issue remains OPEN. Do not claim fixed in newer 0.5.13 source.

## BFRC-10: shader compatibility report on earlier platform

[Issue #10](https://github.com/RogoShum/BruteForceRenderingCulling/issues/10), **0.5.8 Fabric 1.20.1** + Iris shader enable crash. Reported FPS observations and shader incompatibility are secondary user data, not KNEEKURA measured gains. Issue closed without an inspected fix diff. Cannot transfer to 0.5.12 Forge binary.

**Further code to acquire:** shader framebuffer swap logs; exact release 0.5.12 class and Mixin/GL hooks; before/after 0.5.13 diff; GPU capture/repro. No history-adapter import.

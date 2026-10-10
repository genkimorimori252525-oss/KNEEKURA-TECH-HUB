# Distant Horizons 3.2.0-b — evidence-backed source repair window

Track ANCHOR: Minecraft 1.20.1 Forge, **tag `3.2.0b` Git main commit `eb6bf9ae7836bca986b429a28e2a9f94cb45ca77`, Core submodule `a0d2dfe405a8cd8f3c50639378315484e5b56609`**. Official GitLab tag + same-Git-commit accessible via GitHub mirror. Bounded history: release **Jun–Jul 2026** GPU resource/shader fixes, selected parent diffs. Whole Issues/MRs NOT_ACQUIRED; incomplete upstream chronology explicitly recorded.

## DH-GL-VIEWPORT — GL texture leaked after repeated viewport changes

[Actual diff `1a7d3a4e87f...`](https://github.com/DecoderCoder/Distant-Horizons/commit/1a7d3a4e87f84044b2222998db6ef80e4540a602) June 27, 2026; parent `2bffb410a82a8225454d1ce1c4b41be10b4211b0`. In `GlDhMetaRenderer.createAndBindTextures()` **before** simply allocated new `GlDhDepthTexture` and `GlDhColorTexture`. **After** explicitly calls `depthTexture.destroy()` and `nullableColorTexture.destroy()` if previous exist. Maintainer commit describes GL memory leak on viewport change; current 3.2.0b source has the cleanup path.

**Classification:** source DIRECT_OBSERVATION diff, runtime leak/root context MAINTAINER_CLAIM, same JAR binary identity UNKNOWN; KNEEKURA reproduction and fix verification NOT_RUN. Lesson: GL resource replacement on resize must release prior ownership before substitution; test repeated resize/shader reload/virtual camera FBO.

## DH-IRIS-LODTEX — optional LOD textures disabled under Iris

[Actual diff `20f1cc438c...`](https://github.com/DecoderCoder/Distant-Horizons/commit/20f1cc438cbbb656342ea34720cdff5be170cc48), July 7, 2026, parent `f4724012fc7e825a0f1c6522152c4258dca7d831`. `GlDhMetaRenderer` injects IIrisAccessor, adds `irisShadersInactive()` guard to atlas upload/bind and cleanup/unbind, because Iris shaders don't support textured LODs. Same pinned tag source has guards. [Official release notes](https://www.curseforge.com/minecraft/mc-mods/distant-horizons/files/8389142) independently confirm intentional **untextured** LOD fallback for Iris.

Classification: verified code diff but not tested runtime; this is **compatibility adjustment** and known output difference, not a universal performance improvement. Lesson: choose **safe alternate rendering mode** when dependent shader API lacks required metadata.

## Author release and community conflicting evidence

- 3.2.0-b notes mention general ByteBuffer pool improvements and fixes, OpenGL>=3.3, texture atlas support; selected fixed diffs documented, not every release-note claim independently verified.
- [Reddit 2026-08 slowdown discussion](https://www.reddit.com/r/DistantHorizons/comments/1vhazzk/is_anyone_else_getting_far_lower_framerates_with/) involves **different 26.1/26.2** Minecraft versions and GPU; no direct 1.20.1 Forge inference.
- Final acceptance: NO raw original GitLab Issue/PR CAS snapshot, NO server/client game runtime, NO exact release JAR hash, NO measured FPS or VRAM delta.

History import state PARTIAL research only; source mirror pinned via exact official Git SHA + core gitlink, not an invented source equivalence.

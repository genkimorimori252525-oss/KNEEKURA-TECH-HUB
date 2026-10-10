# GPU Tape — bounded upstream history

## GPU-ISSUE-5 — instant Forge Mixin crash in 1.0.5

- Source: [Issue #5](https://github.com/ITsMrToad/GPUBooster/issues/5), opened 2025-01-12, user reported startup crash on Minecraft 1.20.1 Forge using 1.0.5.
- Reported resolution: maintainer says **fixed in 1.0.5.1** ([comment](https://github.com/ITsMrToad/GPUBooster/issues/5#issuecomment-2585551866)). Official [Modrinth Forge 1.0.5.1](https://modrinth.com/mod/gputape/version/1.0.5.1-forge) notes “Fixed instant mixin crash - #5”.
- **No pinned 1.0.5 → 1.0.5.1 Forge repair diff** acquired; actual cause, exact Mixin target, and fix exact bytecode UNKNOWN. Do not substitute newer Fabric GPUTape 1.1.0 `FramebufferMixin` as evidence.
- Both [Forge distribution listing](https://modrinth.com/mod/gputape/version/1.0.5.1-forge) and contradictory [CurseForge metadata](https://www.curseforge.com/minecraft/mc-mods/gputape/files/6200071) are discovery evidence only until binary metadata.
- Reproduction: upstream user REPORTED, KNEEKURA NOT_RUN. Fix verification: NOT_RUN. No history adapter import without immutable raw captured bytes/index IDs.

Scope: one Issue, associated maintainer comment and published release note, source stage `COMPARATIVE_1.1_FABRIC`, distribution `ANCHOR_PENDING_JAR`. This is PARTIAL, not complete upstream history.

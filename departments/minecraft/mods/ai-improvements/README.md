# AI Improvements: Performance Tuning — targeted source review

**Date:** 2026-10-11. **Status:** SOURCE SELECTED FACETS EVIDENCE-BACKED; BINARY / RUNTIME / TPS NOT RUN. Do not confuse with Flemmli97 **Improved Mobs** (a separate content/AI strengthening MOD).

## Source lineage and version traps

- Developer repository: [BuiltBrokenModding/AI-Improvements](https://github.com/BuiltBrokenModding/AI-Improvements).
- **ANCHOR-adjacent version 0.5.2 source:** immutable [`89c89590d8160f332bd2740acd0a67c96f37f00d`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d) with `gradle.properties` `version=0.5.2`, `file_name=AI-Improvements-1.20`, `forge_version=net.minecraftforge:forge:1.20-46.0.12`, `mods.toml` Minecraft `[1.20,1.21)`. Source from 2023-06-10. **Not an exact 1.20.1 Forge 47 build proof**.
- **Binary targeted ANCHOR:** [CurseForge file 4578262](https://www.curseforge.com/minecraft/mc-mods/ai-improvements/files/4578262) advertises the 0.5.2 artifact for 1.20.1 Forge, but exact downloaded filename, SHA-256 and class parity are NOT_VERIFIED here.
- **COMPARATIVE** branch `1.20` latest [`6568bc1343f81c19056b09fada82761fedcbd4d8`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/6568bc1343f81c19056b09fada82761fedcbd4d8) has **changed to NeoForge 1.20.2**, despite branch name. Do not use latest branch head as native 1.20.1.
- **FRONTIER:** latest project source [26.3 `a51cab76acf89099ea3c41393d858f9e061dbe4b`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/a51cab76acf89099ea3c41393d858f9e061dbe4b), NeoForge 26.3; source later than original 0.5.2 and unrelated to 1.20.1 runtime without a backport design.
- Full recursive Git source-path index at `1.20` head has **35 blobs / 19 Java files**; 26.3 source path index **34 blobs / 19 Java**. Selected ANCHOR-adjacent source files inspected: `AIImprovements`, `ModifierSystem`, `ModifierLayer`, `FilterLayer`, `FilteredRemove`, `GenericRemove`, `ConfigMain`, `FixedLookControl`, `FastTrig`, with events/config and historical diff.
- Source `LICENSE`: **MIT (code only)**; 0.5.2 `mods.toml` declares MIT. CurseForge project listing currently says **All Rights Reserved**. Treat the code-only MIT permission and distribution/media listing **separately**; do not redistribute assets/binary or assume parity.

## Core engineering fact

This project **does not globally rewrite vanilla A* pathfinding or speed up all hostile AI Goals**. Its main `EntityJoinLevelEvent` handler visits incoming mobs, conditionally **removes selected Goals** and optionally replaces vanilla `LookControl` with **cached/lookup approximate atan2** math.

Default 0.5.2 config: `remove_look_goal=false`, `remove_look_random=false`, animal task removals default false, `replace_look_controller=true`. With defaults, its primary potential change is **look-controller math**, not mass removal of pathfinding tasks.

### Source-verified feature matrix

| Feature | Source owner | Static finding |
|---|---|---|
| Entity-created tuning | `ModifierSystem.onEntityJoinWorld` | one-time goal filter / look-controller replacement at entity entry |
| Per-class filtering | `ModifierLevel`, `FilterLayer` | mob/fish/squid/cow/chicken/pig/sheep matching, short-circuit filters |
| Task pruning | `ModifierLayer`, `GenericRemove`, `FilteredRemove` | inspect available goals, collect to-remove set, remove after enumeration |
| Config allow/deny scope | `ConfigMain.FilteredConfigValue` | allowlist/exclusion for selected look goal and controller rules |
| Look math | `FixedLookControl` + `FastTrig` | approx atan2 lookup table of 65,536 float entries; state copy from vanilla controller; custom controllers deliberately skipped |
| Gameplay tradeoffs | `ConfigMain` | removing looking/float/panic/breeding etc. can change behavior and visuals, not invisible free performance |
| Profiling | source `src/tools/...MainPerformanceTest` | test harness present in tree, but no verified server TPS benchmark or equivalence |

## Why not blindly combine with KNEEKURA siege

- If a combat mod's `LookAtPlayerGoal` or custom orientation behavior is removed, the attacker may stop turning/aiming correctly, particularly special weapons and multi-emitter bosses.
- Replacing vanilla `LookControl` changes mathematical approximation and animation/aiming precision; it does not prove better CPU time or exact aiming parity.
- `EntityJoinLevelEvent` modifier is capable of removing tasks added by other Mods depending on load order. Disable/allowlist modification for custom siege actors, benchmark changes on vanilla and custom mobs.
- This is a **performance-control component**, not an invasion path planner. Do not confuse with **Improved Mobs**, which adds block-breaking Goals and rewrites path node behavior.

## References

- [Source: 0.5.2 snapshot](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d)
- [Code: ModifierSystem](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/ModifierSystem.java)
- [Code: ModifierLayer](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/editor/ModifierLayer.java)
- [Code: FastTrig](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/FastTrig.java)
- [Author documentation: Modrinth](https://modrinth.com/mod/ai-improvements)
- [Author history: #31](https://github.com/BuiltBrokenModding/AI-Improvements/issues/31)

### Gates remaining

Acquire **0.5.2 Forge 1.20.1** exact released JAR and SHA; verify source-to-binary code, run controlled CPU benchmarks with many siege mobs, evaluate look/aim parity, and verify compatibility with other pathfinder/goal mutators. No loaded-runtime proof or CAS source profile minted.

# NESM + AI Improvements + Epic Siege Mod: phased research continuation

Checkpoint date: 2026-10-11. **Research only**; the user intends to design KNEEKURA Invasion **after** the technology research, so do not prematurely modify or finalize product implementation.

## Completed Phase 1 — exact NESM binary identity and selected bytecode

**DONE**
- Read uploaded `NESM-1.20.1-1.0.1.jar` SHA `7b931b42b42e6f9b349d3eb4f7ad59904d3cfb82afbe8cbfee12448810b31de9`.
- Verified 62,318 bytes/49 entries/39 Java 17 classes. Manifest v1.0.1 vs mods.toml v1.0.0.
- Decompiled **no** archive into shared repository: local `javap` 39/39, selected interpreter-level control-flow audit of `NightmareMain`, `Clocker`, `ESMConfig`, `MobDig/Up/Down`, `MobBuildBridge/Up`, `MobDamageBlock`, `MobPlaceBlock`, `CreeperBreachWalls`.
- Confirmed direct world mutations and lack of an internal blockstate/BlockEntity restoration journal, and detected unused `AllowZombieBuilding`, unused pickaxe eligibility flag and potentially unintended switch fall-through.
- Additional bytecode observation: `isSiegeModeEnabled` is only initialized in `ESMConfig` and not read by any other class's disassembly; the `NightmareMain.isSiegeDay` check instead divides dayTime by 24000 and applies `day % InvadeEveryXDays == 0`; initial interval default 1. Any zero interval config requires validation because modulo by zero is unsafe.
- **No real Minecraft runtime**; no gameplay performance/timing claims.

## Completed Phase 2A — identified source boundaries

- BuiltBrokenModding **AI Improvements** `0.5.2`: [pinned commit `89c89590`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d) targets **1.20 Forge 46**, compatible release advertised for 1.20.1 but no JAR match proven. Branch latest `1.20` head contains later NeoForge 1.20.2, **not** interchangeable.
- Historic **Epic Siege Mod**: [pinned 1.12 source `d02bf54c`](https://github.com/da3dsoul/Epic-Siege-Mod/tree/d02bf54c935b29664bf8058b0e914ebaf49e16dd), **different mod/version/source lineage**; Goal-based digging, pillaring, demolition, extension registry mapped.
- AI Improvements 0.5.2 performs configurable **look/animal Goal removal** and approximated trigonometry `FixedLookControl`; not generic pathfinding acceleration. Default task removals off, look math replacement on. Historical issue #31 led to removal of duplicate LivingSpawnEvent handler.
- Source copyright: NESM ARR; original ESM source permission not established; AI Improvements published source LICENSE **MIT code only** but current listing ARR (binary/media rights separately).

## Phase 2B — next static slices, NOT_DONE

1. NESM original `1.0.0` Forge binary comparison: hash, class delta, constructor and switch changes, StockiesLad deadlock fix attribution with diff.
2. NESM full behavior/state inventory beyond block edits: all spawn/duplication cases, Creeper explosion, target/player filtering, config matrix and damage/path reads.
3. Verify AI Improvements exact 0.5.2 **Forge 1.20.1 release JAR**, find source/build commit equivalence, setup behavior and `FastTrig` cost/accuracy test. Finish remaining source files and dependency closures.
4. Historical Epic Siege complete source provenance/license, pathfinding fix commit `a51465f` parent diff and remaining plugin hooks. If an exact original Nightmare 1.20.4 source repository is found, treat as separately pinned COMPARATIVE target; never infer it equals 1.20.1 port.
5. Complete selected failure/repair histories and minimal CAS evidence with response hashes; no claim of whole-target COMPLETE before required facets.

## Phase 3 — LAB tests, NOT_RUN

- Isolated disposable-world Forge 1.20.1: block break/drop with gamerule off and `AllowZombieGriefing` true/false, `AllowZombieBuilding` false, `EntitiesNeedPickaxesToBreakBlocks` true but no pickaxe, `siegeRecurrence` safe nonzero, dig/build delay 5/10/0.
- Same flat/gapped/walled cell environment with 1, 10, 50, 100 attackers. Record whether actual world edits match bytecode candidate, average/p95 path and world update MSPT, TPS, block collision/lock, startup/event hook overhead. Treat any potential divide-by-zero only in isolated test world.
- Baseline/variant for AI Improvements: no mod, default config, limited look replacement, explicit per-actor filtered Goal removal. Avoid comparison of unrelated world seeds/entity counts. Measure target recognition and boss aim as well as CPU.
- Restore all mutated cells with existing LAB scoped authority; no production world or claimed blanket undo.
- Keep entities' strategy/role policy independent from future reversible terrain journal. No runtime authorization in this report.

## Prior research continuity

[Original exploratory PR #108](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/108) captured earlier `NESM JAR NOT OBTAINED` state and a standalone reversible siege concept. **That historical state was valid then**. This newer exact artifact checkpoint supersedes it for binary availability only, without erasing the research history.

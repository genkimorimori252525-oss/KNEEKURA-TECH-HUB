# Original Epic Siege Mod — historical 1.12 source survey

Date: 2026-10-11. This is a **separate historical COMPARATIVE target**, not the uploaded `NESM-1.20.1-1.0.1.jar` build and not the greenchiss port.

**Repository:** [da3dsoul/Epic-Siege-Mod](https://github.com/da3dsoul/Epic-Siege-Mod) (fork lineage of Epic Siege Mod / Funwayguy), revision [`d02bf54c935b29664bf8058b0e914ebaf49e16dd`](https://github.com/da3dsoul/Epic-Siege-Mod/tree/d02bf54c935b29664bf8058b0e914ebaf49e16dd), branch `1.12`. Git recursive index 85 blobs / 71 Java source files, not truncated. This source targets the old Forge 1.12 ecosystem; no direct 1.20.1 Forge support or JAR equivalence.

## Technical modules inspected

- `ai/ESM_EntityAIDigging.java`: extends **EntityAIBase**, starts when target exists and path is exhausted, traces hit geometry ahead/above/below toward target; attacks only eligible non-infinite-hardness blocks. Dig progress uses item/tool and block strength; final operation is `world.destroyBlock`; re-paths to target after breaking.
- `ai/ESM_EntityAIPillarUp.java`: extends EntityAIBase; when path blocked and target sufficiently high/near, checks adjacent supporting surface and overhead collisions; every **15 Goal ticks** repositions builder above a newly placed default cobblestone or configured material and recomputes path. This is a **reactive pillar tactic**, not proof of fully optimal weighted construction pathfinding.
- `ai/ESM_EntityAIDemolition.java`: optional TNT spawning if mob holding TNT item, target distance under 4 and 200-tick internal cooldown.
- `ai/ESM_EntityAIGrief.java`: separate wandering/grief behavior, random local block scan; filters by block list/light, timing and tool harvest.
- `ai/additions/AdditionDigger.java`, `AdditionPillaring.java`: per-entity class allowlists for attaching these Goals.
- `api/TaskRegistry.java`: registered additions/modifiers as extension point; `MainHandler` integrates at entity join, target and tick event boundaries.
- `ai/hooks/ProxyNavigator.java`: shallow navigator wrapper around normal path set/clear; not proof of novel Minecraft 1.20 path algorithm.

See:
- [Digging Goal](https://github.com/da3dsoul/Epic-Siege-Mod/blob/d02bf54c935b29664bf8058b0e914ebaf49e16dd/src/main/java/funwayguy/epicsiegemod/ai/ESM_EntityAIDigging.java)
- [Pillar Goal](https://github.com/da3dsoul/Epic-Siege-Mod/blob/d02bf54c935b29664bf8058b0e914ebaf49e16dd/src/main/java/funwayguy/epicsiegemod/ai/ESM_EntityAIPillarUp.java)
- [TaskRegistry](https://github.com/da3dsoul/Epic-Siege-Mod/blob/d02bf54c935b29664bf8058b0e914ebaf49e16dd/src/main/java/funwayguy/epicsiegemod/api/TaskRegistry.java)

## Architecture comparison

| Target | Action lifecycle | Terrain edit | Portability limitation |
|---|---|---|---|
| Original Epic Siege 1.12 | installed Goals; `shouldExecute/updateTask` with dig/height checks | permanent `destroyBlock` / `setBlockState` | 1.12 API; not identical to Nightmare port |
| NESM user JAR 1.20.1 | server LivingTickEvent instantiates behavior classes on tick/modulo | direct `destroyBlock(true)` and `setBlockAndUpdate` | binary now inspected; no exact upstream source equivalent established |
| Improve Mobs 1.20.1 | path evaluator treats breakable candidate as walkable at malus; BlockBreakGoal executes | conditional break; limited time-delayed BlockState restoration | Mixins and saved-data semantics |
| Zombies Break & Build 1.20.1 | state + tactic executor for stuck/bridge/pillar | timed breaking/building stores + optional NBT | different source and LGPL license |

**No original source should be copied to a 1.20.1 Forge product without an independent rights audit.** The GitHub tree's license file was not established in this investigation. Performance/TPS/interaction with modern Mods NOT_RUN.

## Selected source repair history

This historical branch's [commit a51465f...](https://github.com/da3dsoul/Epic-Siege-Mod/commit/a51465f74452f74e8b605625986b980d47fe1994) describes fixing vanilla wandering AI latency and pathfinding too often; diff has **not** yet been fully reviewed for the exact causal chain. Mark as **DISCOVERED_NOT_REVIEWED**, not a verified fix. Future separate `FAILURE-REPAIR-HISTORY.md/json` should trace issue/commit parent, callers and side effects.

## Suggested next phase (no implementation now)

Build comparable AI decision traces of target+path+dig/pillar preconditions for NESM vs historical ESM vs Improve Mobs vs ZBB, then evaluate additional CPU/blocked attempts and per-cell edit safety. Keep the future `KNEEKURA Invasion` product plan deferred.

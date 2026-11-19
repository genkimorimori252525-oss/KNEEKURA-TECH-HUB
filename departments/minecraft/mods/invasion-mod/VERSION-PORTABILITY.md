# Version Portability — 1.7.10 to 1.20.1 Forge anchor

## Principle

The adaptation target is **Minecraft 1.20.1 + Forge**. The current public 1.20.1 branch already demonstrates that the important siege ideas survive the API transition, but it also shows why direct source copying is the wrong approach.

| Invariant | 1.7.10 implementation | 1.20.1 implementation | Port verdict |
|---|---|---|---|
| action-bearing path node | custom \`PathNode(action)\` | \`PathAction\` mixed into vanilla \`Node\` | **KEEP concept; use modern expression** |
| A*-like search | custom static synchronized \`PathfinderIM\` | vanilla \`PathFinder\` subclass / node evaluator | **REWRITE / do not port singleton** |
| dig-through route | destructible cell + \`DIG\`/blocked callback | mineable blocked node becomes WALKABLE+\`DIG\`; \`MineBlockGoal\` | **KEEP** |
| engineer bridge | custom successor + \`NavigatorEngy\` | \`BuilderIMMobNavigation.NodeMaker\` + action handler | **KEEP** |
| scaffold choice | AttackerAI candidate re-search | \`ScaffoldGenerator\` headless re-search | **KEEP strongly** |
| density avoidance | \`TerrainDataLayer\` + per-20-tick rebuild | collision/data wrapper + amortized 20-tick rebuild | **KEEP, amortize** |
| timed world edit | \`TerrainModifier\` callback list | typed-status \`TerrainModifier\` | **KEEP, modern status contract** |
| block strength/path cost | block ID maps | tags + config + cached Lookup | **KEEP, data/tag driven** |
| fixed wave scripting | hardcoded first 11 + scaled extension | legacy wave classes retained plus budget phase planner | **KEEP when authored rhythm matters; budget model optional** |
| sector spawn fallback | \`WaveEntry.reviseSpawnAngles\` | retained with blocked-spawn retry | **KEEP** |
| spawn-point generation | large synchronous ring/elevation scan | incremental probe budget + layer policy | **MODERNIZE** |
| restore scheduler | 100 ms no-spawn replay | modern state/recovery model | **prefer explicit state** |
| entity sync | DataWatcher + tile S35 packet | modern entity/block-entity/network APIs | **API rewrite** |
| renderer registration | FML client registry + immediate render classes | version-specific renderer APIs | **API rewrite; unrelated to siege invariant** |

## 1.20.1 anchor evidence

Pinned source:
[kevintrini2811/Invasion-Mod@aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10](https://github.com/kevintrini2811/Invasion-Mod/tree/aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10)

Important files:

- \`entity/pathfinding/path/PathAction.java\`
- \`entity/pathfinding/path/ActionablePathNode.java\`
- \`mixin/PathNodeMixin.java\`
- \`entity/pathfinding/DynamicPathNodeNavigator.java\`
- \`entity/pathfinding/IMLandPathNodeMaker.java\`
- \`entity/pathfinding/IMMobNavigation.java\`
- \`entity/pathfinding/BuilderIMMobNavigation.java\`
- \`entity/ai/goal/MineBlockGoal.java\`
- \`entity/ai/builder/TerrainModifier.java\`
- \`nexus/ai/AttackerAI.java\`
- \`nexus/ai/scaffold/ScaffoldGenerator.java\`
- \`nexus/spawns/IMWaveSpawner.java\`

## Recommended KNEEKURA extraction order

1. **PathAction carrier contract** independent of a specific mob.
2. **Node-evaluator hooks** for DIG/BRIDGE and cost overlays.
3. **Terrain job executor** with explicit result status and ownership.
4. **Navigator action barrier**: never allow path advancement to skip pending work.
5. **Density overlay** with a bounded update budget.
6. **Scaffold counterfactual planner** using a headless/stand-in path query.
7. **Wave timeline/sector abstraction** and spawn failure accounting.
8. Optional specialist-role cooperation.

## Semantic risks

### Vanilla path-following may skip action nodes

Modern \`IMMobNavigation\` contains special handling because vanilla navigation can consider a nearby actionable node reached and advance past it. Any independent implementation must treat an action node as a barrier until its terrain transaction succeeds.

### World snapshots and hypothetical edits

Counterfactual path planning must not mutate the live world. Use a read-only overlay/view to mark hypothetical scaffolds or tactical costs.

### Main-thread world mutation

Path search can be optimized or prepared away from block mutation, but terrain edits themselves must respect Minecraft server-thread rules. Do not infer thread safety from the modern source's executor declaration alone.

### Cost composition

Avoid double-counting: vanilla node malus, Invasion material cost, mob-density cost and work cost all influence search. Tests should pin whether a penalty is multiplicative or additive.

### Gamerule and protected blocks

Both old and modern code treat \`mobGriefing\` and unmodifiable blocks as part of the navigation contract. A planner must not generate a route that its executor is forbidden to realize.

## FRONTIER

Public NeoForge 26.3 source is pinned at [fce5d30b74f804ae90814c7a10cdff255ba80363](https://github.com/kevintrini2811/Invasion-Mod/tree/fce5d30b74f804ae90814c7a10cdff255ba80363). It remains useful for evolution/performance ideas, but ANCHOR and FRONTIER are diverged branches. Do not back-copy a 26.3 API call into 1.20.1 without an explicit translation.

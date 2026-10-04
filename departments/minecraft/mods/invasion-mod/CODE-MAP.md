# Code Map — Invasion Mod siege systems

## Legacy 1.7.10 control graph

\`\`\`text
BlockNexus / catalyst inventory
        |
        v
TileEntityNexus
  |-- mode + HP + bound players + NBT
  |-- IMWaveBuilder -------------------------+
  |-- IMWaveSpawner                         |
  |-- AttackerAI                            |
  |                                         |
  +--> Wave -> WaveEntry -> EntityPattern --+
                         -> EntityConstruct
                         -> MobBuilder -> EntityIM*
                                           |
                                           v
                                    Goal/task selection
                                           |
                              NavigatorIM / NavigatorEngy
                                           |
                                PathfinderIM (A*-like)
                                           |
                   PathNode(x,y,z, PathAction)
                         |              |
                  movement edge      siege edge
                                        |
                      DIG / BRIDGE / LADDER / TOWER / SCAFFOLD
                                        |
                 TerrainDigger / TerrainBuilder
                                        |
                             TerrainModifier
                                        |
                                  World edit
\`\`\`

## Core legacy files

| Subsystem | Pinned files | Important role |
|---|---|---|
| Nexus lifecycle | \`nexus/TileEntityNexus.java\`, \`BlockNexus.java\` | activation modes, health, waves, persistence, bound players |
| wave composition | \`IMWaveBuilder.java\`, \`Wave.java\`, \`WaveEntry.java\` | timing, pools, bursts, directional sectors |
| entity construction | \`EntityPattern.java\`, \`EntityConstruct.java\`, \`MobBuilder.java\` | separates schedule choice from live entity instantiation |
| spawn geometry | \`IMWaveSpawner.java\`, \`SpawnPointContainer.java\` | ring/elevation probing, angular spawn points, retry |
| route search | \`PathfinderIM.java\`, \`NodeContainer.java\`, \`PathNode.java\` | custom costed A*-like search and partial paths |
| navigation | \`NavigatorIM.java\`, \`NavigatorEngy.java\` | follow/repath/stuck detection/action execution |
| terrain work | \`TerrainModifier.java\`, \`TerrainDigger.java\`, \`TerrainBuilder.java\` | timed reach-bounded world edits |
| coordination | \`entity/ai/AttackerAI.java\`, \`Scaffold.java\`, \`TerrainDataLayer.java\` | density overlay and scaffold planning |
| role AI | \`EntityAIGoToNexus.java\`, \`EntityAIAttackNexus.java\`, \`EntityAIWaitForEngy.java\`, \`EntityAITargetOnNoNexusPath.java\` | objective hierarchy and engineer cooperation |
| rendering | \`client/ProxyClient.java\`, render/model/animation tree | entity render registration and custom keyframe system |
| networking | \`TileEntityNexus.java\`, Entity DataWatcher fields | old active sync; generic PacketPipeline source is commented out |

Pinned source root:
https://github.com/UnstoppableN/Invasion-mod/tree/644a52ddea104c206d022bef9edc135c060cba1d/src/main/java/invmod

## Legacy path search

\`PathfinderIM\` is a custom A*-like implementation:

- open set: \`NodeContainer\` binary min-heap;
- g cost: \`examining.totalPathDistance + entity.getBlockPathCost(...)\`;
- heuristic: Manhattan-like absolute deltas with a small Z weighting;
- successors supplied by the entity, allowing different mob movement grammars;
- node identity includes \`PathAction\`, so the same coordinate can represent a different operation;
- node budget exhaustion returns a path to the closest reached node instead of always returning null.

Important limit: \`PathfinderIM.createPath\` is a static synchronized method using one singleton pathfinder. This prevents simultaneous mutation of its internal maps/heap but serializes all path searches. The modern anchor does not preserve that implementation choice.

## Construction actions

The legacy engineer navigator resolves action nodes before movement advances:

- ladder action -> \`TerrainBuilder.askBuildLadder\`
- \`BRIDGE\` -> \`askBuildBridge\`
- \`SCAFFOLD_UP\` -> \`askBuildScaffoldLayer\`
- ladder-tower actions -> \`askBuildLadderTower\`

The navigator enters a waiting/holding state until the terrain callback finishes. This is the key separation between **planning an edit** and **executing an edit**.

Source:
https://github.com/UnstoppableN/Invasion-mod/blob/644a52ddea104c206d022bef9edc135c060cba1d/src/main/java/invmod/common/entity/NavigatorEngy.java#L37-L87

## Counterfactual scaffold planner

\`AttackerAI.findMinScaffolds\` first asks a special \`Scaffold\` pather for a route that can include \`SCAFFOLD_UP\`. Candidate vertical segments are extracted. When multiple candidates exist, it re-runs pathfinding while marking candidates as if they already existed, then selects a route-enabling / low-cost intervention.

This is a general technique: **search -> infer required infrastructure -> inject hypothetical infrastructure -> re-search -> choose the smallest useful intervention**.

Source:
https://github.com/UnstoppableN/Invasion-mod/blob/644a52ddea104c206d022bef9edc135c060cba1d/src/main/java/invmod/common/entity/ai/AttackerAI.java#L87-L180

## Crowd-aware terrain overlay

Every 20 ticks the old \`AttackerAI\` builds a coordinate-density map for Nexus mobs, capped at seven. The terrain wrapper exposes those extra values to path cost without changing real blocks.

Ordinary mob path cost adds \`density * 3\`; Pig Engineer uses a lower density penalty. This makes attackers spread while allowing the route-builder to push through congestion.

## Modern 1.20.1 translation

The native 1.20.1 source replaces the custom pathfinder core with extensions around vanilla navigation:

- \`PathNodeMixin\` adds \`PathAction\` to vanilla \`Node\`;
- \`ActionablePathNode\` reads/writes that action;
- \`DynamicPathNodeNavigator\` extends vanilla \`PathFinder\`;
- \`IMLandPathNodeMaker\` turns mineable blocked cells into \`WALKABLE + DIG\`;
- \`BuilderIMMobNavigation\` adds bridge nodes for traversable gaps;
- \`IMMobNavigation\` guarantees terrain actions execute before vanilla path-following can skip them;
- \`MineBlockGoal\` makes block clearing a first-class goal with failure/repath policy;
- \`ScaffoldGenerator\` preserves the old counterfactual scaffold-selection idea using a headless vanilla pathfinder.

Anchor source:
https://github.com/kevintrini2811/Invasion-Mod/tree/aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10/src/main/java/com/invasion

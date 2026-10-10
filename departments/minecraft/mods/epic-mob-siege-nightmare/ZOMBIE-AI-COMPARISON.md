# Siege AI research — two distinct ways to solve inaccessible targets

Sources: [old Invasion Mod `0bccc286...`](https://github.com/Doenerstyle/Invasion-Mod/tree/0bccc286114ffae9f9224892ab1fe451fc97ef08) versus [Zombies Break & Build 1.20.1 `73a80226...`](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3). **Neither is the exact Epic Mob Siege: Nightmare binary.**

## Explicit path action: Invasion Mod

- `PathAction` enumerates `DIG`, `BRIDGE`, `LADDER_UP`, `LADDER_TOWER_UP_{PX,NX,PZ,NZ}`, `SCAFFOLD_UP`, and `SWIM`.
- `PathfinderIM` constructs nodes that store the action and expands using cost from `IPathfindable.getBlockPathCost`; range and exploration count are bounded.
- `TerrainBuilder` maps construction proposals to `ModifyBlockEntry` queued tasks, different materials and build-time costs; team-support `EntityAIWaitForEngy` interacts with specialist pig engineer.
- Strength: planner can compare **route cost including building** and actors can specialize; supports Nexus-defense fantasy.
- Weakness (design implication, not measured criticism): rich action graph grows branching/CPU and old Java APIs are not 1.20.1 APIs.

Locators:
- [PathAction.java](https://github.com/Doenerstyle/Invasion-Mod/blob/0bccc286114ffae9f9224892ab1fe451fc97ef08/src/main/java/invmod/common/entity/PathAction.java)
- [PathfinderIM.java](https://github.com/Doenerstyle/Invasion-Mod/blob/0bccc286114ffae9f9224892ab1fe451fc97ef08/src/main/java/invmod/common/entity/PathfinderIM.java)
- [TerrainBuilder.java](https://github.com/Doenerstyle/Invasion-Mod/blob/0bccc286114ffae9f9224892ab1fe451fc97ef08/src/main/java/invmod/common/entity/TerrainBuilder.java)

## Conditional tactical action: Zombies Break & Build

At `1.20.1` source:
- `MainCommon.onJoin` adds `BreakAndBuildGoal` to compatible `PathfinderMob` and separate nearest-player target goal where missing;
- `BreakAndBuildGoal` owns `MobStateHandler` + `ActionExecutor`;
- `BreakAndBuildState` has four tactics: adjust-height, bridge-to-target, clear obstacles, mitigate dangerous blocks;
- it raises action priority if native navigation is stuck, a 30-tick/1-block stuck detector trips, the path is null for >=5 checks, the partial path endpoint is near, or an exhausted path remains far from target; if native path reaches target, tactics have low priority;
- `AdjustHeightToTargetTactic` actively jumps and places a foothold beneath the mob; `BridgeToTargetTactic` computes the next block-boundary crossing from the mob and target bounding boxes and places support in front;
- `ClearObstaclesToTargetTactic` looks for colliding blocks around the mob's hitbox in target-facing direction;
- `BreakAction` uses block-health + mob/tool-scaled damage, cooldown, tracked damage, no-unloaded-chunk writes, and `ServerLevel.destroyBlock`; `BuildAction` checks replaceability and stores old `BlockState` / optional block-entity NBT.

Strength: lightweight use of vanilla navigation, clear tactical escalation, separate actions and transients. Known community [issue #1](https://github.com/XTiK555/ZombieBreakAndBuild/issues/1) reports crash during large hordes (closed report, reproduction/fix unverified here). Do not assume universal correctness for high-concurrency writes.

Selected source locators:
- [BreakAndBuildState.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/state/states/BreakAndBuildState.java)
- [BridgeToTargetTactic.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/state/tactic/tactics/BridgeToTargetTactic.java)
- [AdjustHeightToTargetTactic.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/state/tactic/tactics/AdjustHeightToTargetTactic.java)
- [BreakAction.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/action/actions/breakk/BreakAction.java)

## Recommended future KNEEKURA architecture

**Hybrid staged planner**, not direct code combination:
1. Let vanilla `PathNavigation` attempt a safe route and return path quality.
2. If blocked, generate **bounded candidate breach/bridge/pillar** actions by short local tactical probe.
3. Score each candidate using estimated progress to Nexus, time, resource/block hardness, claim/block safety, collision risk, and pending rollback budget. Specialists have distinct allowed action sets.
4. Reserve cells/claims in a group coordinator so a horde cannot simultaneously mine/replace the same block.
5. Only the authoritative server mutation adapter is permitted to execute, and only after the **durable original-state journal entry** is confirmed.
6. Repath after each success/failure; never lock the entire server while pathing.

Use fallback to explicit action-augmented path nodes only when local tactical probes demonstrably fail, and keep the old Invasion-specific path weights as **comparative theory**, not a default constant.

## AI measurement data to collect in LAB

`actorId`, `waveId`, `NexusPosition`, `pathIsDone`, `pathCanReach`, `stuckTicks`, `candidateAction`, `estimatedCost`, `ownerReservation`, `targetBlockStateHash`, `decisionReason`, `preJournalReceiptId`, `mutationOutcome`, `newPathCost`. Test at 1 / 10 / 50 / 100 active attackers and a defended base, with actual TPS and memory measurements—not presumed.

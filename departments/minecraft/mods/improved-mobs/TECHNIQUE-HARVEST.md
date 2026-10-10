# Improved Mobs — concept-level technique harvest

**Status:** evidence-backed source concepts for later architecture review; **NOT implementation decisions** for KNEEKURA Invasion. License: All Rights Reserved. Do not copy third-party code.

| Capability | Evidence | Reusable **concept** | Suitability / concerns |
|---|---|---|---|
| Route planning that sees breakable walls as future free space | ANCHOR `GroundNodeMixin`, `PathFindingUtils` | route feasibility includes demolition cost; break action makes plan real | HIGH relevance, but Mixins fragile and CPU-intensive at horde scale |
| Collision-aware dig direction and size | `BlockBreakGoal.breakAOE/getDiggingLocation` | examine volume required by attacker's bounding box, orient to next path node | HIGH; avoid arbitrary harmful edits |
| Adaptive fallback between ground and flight | `FlyRidingGoal.checkFlying` | compare route reachability and distance-to-target across locomotion modes | HIGH; defer mount transitions and limit vehicles |
| Ladder as explicit path option | `createLadderNodeFor`, `LadderClimbGoal` | vertical path node / climb execution distinction | HIGH for existing ladders, **not** a tower-building algorithm |
| Timed ruined-block repair | `BlockRestorationData` | save original BlockState, expiration time, per-chunk pending edits | REFERENCE ONLY; 0 default, lacks block entity NBT and strict conflict handling |
| Difficulty progression by world/time/player/range | `DifficultyData`, `DifficultyConfig` | decouple encounter hardness from arbitrary mob spawn values | MEDIUM; avoid time-skip abuse and combat unpredictability |
| Conditional goal overlay for vanilla/modded Mob | `EventCalls.onEntityLoad` + EntityFlags | add selected AI to existing Mob types by policy and type/tag | HIGH, subject to compat and ownership checks |
| Mob item tactical usage | `ItemUseGoal` + `ItemAIs` | cooldown-driven weapon actions per class/item | HIGH; TNT/lava excluded from simple terrain rollback |
| Enemy looting | `StealGoal` and opened-inventory marker | explicit interaction eligibility and resource-scoped behavior | OPTIONAL; may undermine defense-building motivation |
| Search-local path type memoization | `WalkNodeEvaluatorMixin` etc. | cache expensive raw path types and clear on search completion | PERFORMANCE CANDIDATE, runtime value and Mixin conflicts unproven |
| Per-entity datapack overrides (FRONTIER) | 1.21.1 `EntityOverridesManager` | external rule set for per-mob abilities, block allowlists, attributes | HIGH conceptual value, direct Forge 1.20.1 port NOT_AVAILABLE |

## Strong differences from other MODs

- **Improved Mobs**: converts candidate breakable blocks into walkable path search nodes; no source-backed temporary scaffold planner. Does have a **limited restoration** mechanism.
- **Zombies Break & Build**: explicit reactive strategies for pillar, bridge, clearing obstacles; two separate timed block stores with old NBT, but not guaranteed full world rollback.
- **Historical Invasion Mod**: DIG/BRIDGE/SCAFFOLD already part of its explicit path action graph and siege-role cooperation, on an older Minecraft API.
- **Raids: Enhanced**: boss wave addition, unique combat archetypes and multi-weapon systems; not a generic dynamic block-aware planner.
- **Epic Mob Siege: Nightmare**: public behavior suggests destructive/constructive attackers; exact 1.20.1 binary algorithm still needs direct JAR proof.

This matrix is a **research menu**, not a plan to mix all four global AI mutators into the same runtime. Two mods injecting `WalkNodeEvaluator` or attempting to break the same cell may cause conflicts; the observed issue tracker includes reported performance and compatibility problems.

## Caveats before independent code adoption

1. Avoid copying global Mixins without verifying direct target 1.20.1 mapped method signatures and other mods' injection order.
2. Preserve a distinct world-mutation permission boundary and exact original-state restoration (BlockEntity NBT/claims) if required later. Improved Mobs' existing recovery is not sufficient.
3. Evaluate horde performance in real 1.20.1 Forge with closed-loop observations (1/10/50/100 attackers, NBT, tick timings, entity target mixes).
4. Separate difficulty knobs, attack behavior and actual siege objective so each Mob can have different strategic roles.
5. Multi-version ideas must keep ANCHOR and FRONTIER immutable SourceSnapshots; current checkout's master cannot be silently substituted.
6. Record any adopted concept as a new independent implementation with tests and source credit; ARR prohibits simply uploading upstream method bodies.

## Future research gates, not scheduled implementation

- Exact release artifacts `improvedmobs-1.20.1-1.13.7-forge.jar` and TenshiLib bytes/hash;
- verify source-binary equivalence by bytecode and resource inventory;
- static/experimental conflict matrix: Raids Enhanced, Epic Mob Siege, Zombies Break & Build, Enhanced AI, Epic Fight, Flan/claims;
- controlled failure injection: on-damage drop, Mob griefing false, BlockEntity/door/fence multiblock, delayed chunk load, player conflicting edits, large horde;
- overlay trace integration with KNEEKURA Water Tank / Decision Observatory using its existing authorized LAB test contracts only.

**Do not establish the final KNEEKURA Invasion architecture during this research phase.**

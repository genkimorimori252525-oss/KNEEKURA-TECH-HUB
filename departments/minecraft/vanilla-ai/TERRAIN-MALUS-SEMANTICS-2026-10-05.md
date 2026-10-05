# Terrain classification and malus — exact ANCHOR semantics

This completes the detailed original B5 static explanation together with [Pathfinding](PATHFINDING.md). Source authority is the same hashed Minecraft1.20.1 Forge47.2.0 resolved development artifact in the [method/field ledger](PATH-TERRAIN-BYTECODE-LEDGER-2026-10-05.json). It does not establish runtime-loaded transformed equivalence, all custom subclasses, native branches or zero observer effect.

## Declared type defaults

All25 declared `BlockPathTypes` enum constants and constructor malus values in this artifact:

| Default | Types |
|---|---|
| −1 | BLOCKED, POWDER_SNOW, FENCE, LAVA, UNPASSABLE_RAIL, DAMAGE_OTHER, DOOR_WOOD_CLOSED, DOOR_IRON_CLOSED, LEAVES |
| 0 | OPEN, WALKABLE, WALKABLE_DOOR, TRAPDOOR, DANGER_POWDER_SNOW, RAIL, DOOR_OPEN, COCOA, DAMAGE_CAUTIOUS |
| 4 | BREACH |
| 8 | WATER, WATER_BORDER, DANGER_FIRE, DANGER_OTHER, STICKY_HONEY |
| 16 | DAMAGE_FIRE |

This Forge artifact implements `IExtensibleEnum`; its unextended `create(String, float)` throws `Enum not extended`. The25 declared constants do not prove that loaded MOD extensions can add no runtime values. `getDanger` maps fire categories to DANGER_FIRE, other damage/danger to DANGER_OTHER, and LAVA to DAMAGE_FIRE; other categories return null. A type name is neither a universal impassability decision nor a damage event.

## Effective Mob values and actual node values

Base `Mob.getPathfindingMalus(type)` uses a controlled vehicle Mob when that vehicle's virtual `shouldPassengersInheritMalus()` permits it; otherwise it uses the selected Mob. It reads that Mob's override map, falling back to the enum default. Base inheritance permission is false; Strider overrides it to true. The base setter writes its own map, so a passenger's own write does not necessarily change an inherited getter result. A custom getter/setter can override these bodies. Exposed cached own-map contents, an original virtual getter return and the reason/provenance of that return remain different observations.

Concrete constructor examples explain why a default table alone is insufficient:

| Owner | Explicit constructor calls |
|---|---|
| Bee | DANGER_FIRE−1, WATER−1, WATER_BORDER16, COCOA−1, FENCE−1 |
| Turtle | WATER0; DOOR_IRON_CLOSED, DOOR_WOOD_CLOSED and DOOR_OPEN−1 |
| Frog | WATER4, TRAPDOOR−1 |
| Strider | WATER−1; LAVA, DANGER_FIRE and DAMAGE_FIRE0; passengers may inherit its malus |
| Warden | UNPASSABLE_RAIL0; DAMAGE_OTHER, POWDER_SNOW and LAVA8; DAMAGE_FIRE0 |

These are inspected constructor calls, not an exhaustive all-Mob override catalog or a promise of immutable lifetime values. Search preparation also changes values: Amphibious calls WATER0 and temporarily saves effective WALKABLE/WATER_BORDER then sets6/4; cleanup restores those two numeric values but has no WATER restore in these inspected bodies. Restoring a numeric effective value into an own map does not restore prior absence or inherited provenance. Custom callbacks or overrides can change the resulting state. A regional observer must not call prepare/done to obtain apparently correct costs.

Node `costMalus` can differ further. Walk/Fly/Swim use max(existing node cost, getter result); Fly adds1 on WALKABLE, Swim adds8 for empty fluid, shallow-preferring Amphibious adds1 to emitted deep-water neighbors. Revisited cached nodes can accumulate these additions. A getter return of0 does not prove node cost0. Negative effective values normally reject creation, but Walk's fallback start/cardinal-current-negative escape and closed/blocked sentinels mean “every negative cell is absent from every search structure” is false. Finder acceptance independently checks walked distance/open membership/g improvement.

## Raw ground classification and precedence

`WalkNodeEvaluator.getBlockPathTypeRaw(BlockGetter, BlockPos)` first calls the Forge block-state `getBlockPathType(level, pos, null)` callback; a non-null result wins. The Mob argument here is null. It then checks:

1. Air → OPEN; trapdoor tag/lily pad/big dripleaf → TRAPDOOR; powder snow → POWDER_SNOW; cactus/berry bush → DAMAGE_OTHER; honey → STICKY_HONEY; cocoa → COCOA; wither rose/pointed dripstone → DAMAGE_CAUTIOUS.
2. A fluid `getBlockPathType(level, pos, null, false)` callback before vanilla lava/fire/door/rail classification. A non-null callback wins; otherwise lava fluid → LAVA, burning block → DAMAGE_FIRE.
3. Open door → DOOR_OPEN; closed hand-openable door → DOOR_WOOD_CLOSED; other closed door → DOOR_IRON_CLOSED. Rail → RAIL; leaves → LEAVES. Fences/walls/closed fence gates → FENCE; an open gate proceeds to the remaining classification.
4. A non-land-pathfindable state → BLOCKED. Otherwise the loggable-fluid callback with final argument true can win; water → WATER, other cases → OPEN.

`isBurningBlock` includes the FIRE tag, lava block, magma, lit campfire and lava cauldron. These classification categories do not establish that the Mob took damage, cannot withstand it, or rejected this location. MOD callbacks can supply a different type and can execute custom logic; the static query is not purely a table lookup.

## Support and neighboring hazards

The static ground classifier starts with the raw cell. For OPEN at or above min-height+1 it classifies the block below: solid support can yield WALKABLE, while raw WALKABLE/OPEN/WATER/LAVA below keeps OPEN. DAMAGE_FIRE, DAMAGE_OTHER, STICKY_HONEY and DAMAGE_CAUTIOUS support propagate; POWDER_SNOW support yields DANGER_POWDER_SNOW.

Only a resulting WALKABLE cell runs the neighboring-hazard scan. The scan covers offsets −1..1 in X/Y/Z while excluding the whole same-XZ vertical column (24 surrounding cells). At each neighbor it first offers the Forge block adjacent-type callback, then fluid adjacent-type callback. A non-null result returns immediately. Otherwise cactus/berry → DANGER_OTHER; burning → DANGER_FIRE; water → WATER_BORDER; wither rose/dripstone → DAMAGE_CAUTIOUS. It returns the first encountered match in loop order, not an aggregate maximum-risk field. Fly applies its own below-cell rules and invokes the neighbor scan for both WALKABLE and OPEN. Amphibious WATER classification instead inspects six raw adjacent cells for BLOCKED.

## Mob extent, doors, rails and collision

Mob-aware Walk classification evaluates an integer volume sized `floor(width+1) × floor(height+1) × floor(width+1)`, not just the origin cell. Each type passes through `evaluateBlockPathType`. A wooden closed door becomes WALKABLE_DOOR only when both evaluator open-doors and pass-doors flags are true; an open door with pass-doors=false becomes BLOCKED. Closed iron doors are not promoted by that branch. RAIL becomes UNPASSABLE_RAIL unless the Mob's current block or block below is rail. This depends on the Mob's location, not merely the queried rail cell.

Volume aggregation gives FENCE precedence, then UNPASSABLE_RAIL. Otherwise an encountered negative effective type is returned, or the type with greatest effective malus is selected (including enum-order ties). The origin OPEN special case with zero selected cost and width<=1 can remain OPEN. Fly aggregation differs and must retain its evaluator label. Ground/Flying Navigation's `canOpenDoors()` getter in this artifact actually delegates to evaluator `canPassDoors()`; the evaluator's own open/pass flags remain distinct. Reading a misleading Navigation method name is not proof of the open-door flag.

Classification/flags are only part of acceptance. Walk uses support collision-shape height, jump/step/fall limits, sampled swept AABBs from partial-collision current nodes, narrow-body step AABBs, and cached `region.noCollision(mob, box)`. Water/air evaluators use their own volume/neighbor rules. A single aerial/aquatic Navigation ray is not a full swept bounding-box guarantee. FENCE or a negative default alone is not a substitute for the actual executing evaluator and its Mob-specific values.

## Regional query versus original evaluation

The existing [bounded ground query](TERRAIN-GROUND-QUERY-2026-10-03.md) samples a requested plane using the static ground classifier, cached own override/default data and loaded-chunk-only input. It is intentionally separate from original search callbacks and effective getter-return evidence. Its historical validation boundary remains the record of that slice; subsequent native records are additive, not retroactive changes to the old run.

Retained diagnosis must distinguish:

- observed block/fluid input and static ground classification;
- declared default and own cached override;
- original effective getter return, with provenance unknown where not exposed;
- original evaluator/neighbor emission and actual node cost;
- accepted Finder relaxation, returned Path and adopted/current Navigation state;
- actual sampled motion and any separately captured result.

A queried coordinate need not have been evaluated by the Mob's search. Cached candidates, emitted neighbors and accepted relaxations are different stages. Unknown/capped/unavailable fields remain explicit; no second search, callback replay, chunk loading or inferred rejection is needed to fill them. Numeric cost/type/status must remain available alongside color/pattern encodings in views.

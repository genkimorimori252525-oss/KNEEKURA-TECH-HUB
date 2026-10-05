# Pathfinding and malus — Minecraft 1.20.1 ANCHOR

Evidence: the original [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json) and additive [Path/terrain method ledger](PATH-TERRAIN-BYTECODE-LEDGER-2026-10-05.json). The latter records31 exact class hashes,302 selected method descriptors/disassembly slices and116 fields from the same resolved Forge47.2.0 development artifact. [Research validation and boundaries](PATH-TERRAIN-RESEARCH-2026-10-05.md) distinguish static explanation from retained native evidence. This is the original B4/B5 research, not a new runtime hook.

## Navigation families and ownership

Scanning superclass chains for all7,108 Minecraft owners finds11 PathNavigation-family owners, including the base. Anonymous Bee/Warden classes are included by inheritance rather than a name suffix. This inventory is complete for the hashed resolved artifact; loaded transformations and third-party roots are separate.

| Actual owner | Evaluator / relevant differences from base |
|---|---|
| `PathNavigation` | Abstract family root; owns PathFinder, selected Path/index, target, reach range, recompute and stuck state. Constructor fixes Finder's visited-node base to `floor(FOLLOW_RANGE * 16)`; later searches read the current follow range and apply the current multiplier. |
| `GroundPathNavigation` | WalkNodeEvaluator with pass-doors enabled; update allowed on ground, in liquid or while a passenger. Air/solid target adjustment, float-water surface and optional avoid-sun trimming are ground-specific. Entity-target creation forwards to the BlockPos overload rather than base entity region settings. |
| `FlyingPathNavigation` | FlyNodeEvaluator with pass-doors enabled; update allowed when floating in liquid or not a passenger. Its own tick sends the raw next-node Y to MoveControl rather than base ground-Y correction. Direct movement uses the collider ray with fluids included. |
| `WaterBoundPathNavigation` | SwimNodeEvaluator; allow-breaching enabled only for Dolphin in `createPathFinder`. Update requires liquid unless breaching is allowed. Uses mid-body Y and raw next-node Y, ignores `setCanFloat`, and ray-tests with fluids excluded. |
| `AmphibiousPathNavigation` | AmphibiousNodeEvaluator(false), pass-doors enabled; update always permitted. Uses mid-body Y/raw target Y; direct movement ray is available only in liquid, with fluids excluded. `setCanFloat` is a no-op. Stable destination requires a non-air block below. |
| `WallClimberNavigation` | Extends Ground; retains a separate `pathToPosition`. `moveTo(Entity, speed)` returns true even when path creation returns null, then tick can send that destination directly to MoveControl. An absent/done Path does not prove stopped movement. |
| `Bee$1` | Anonymous Flying subclass: stable destination needs non-air below; its tick skips `super.tick()` while pollination is active. Creation sets open-doors=false, float=false and pass-doors=true. |
| `Turtle$TurtlePathNavigation` | Amphibious subclass: while travelling, stable destination must be an actual WATER block; otherwise it needs non-air below. |
| `Frog$FrogPathNavigation` | Amphibious subclass using FrogNodeEvaluator(true); disallows WATER_BORDER corner cutting in addition to base exclusions. |
| `Strider$StriderPathNavigation` | Ground subclass using Walk; treats LAVA/DAMAGE_FIRE/DANGER_FIRE as valid in its `hasValidPathType` helper and accepts lava as a stable destination. Do not infer a new direct-movement implementation from that helper. |
| `Warden$1` | Anonymous Ground subclass using Walk and `Warden$1$1`, an anonymous PathFinder whose protected edge `distance` uses XZ distance. The base heuristic/reach/distance-limit operations still use their own Node methods. |

`Mob.getNavigation()` and MoveControl ownership can also delegate to a controlled vehicle. The class of the selected entity alone does not establish which navigation/control object executes. Unknown/custom classes retain their actual identity and generic capability boundary.

## Path creation, adoption and recomputation

Base BlockPos/Set/Stream creation uses region offset8 without upward origin shift; base Entity creation uses16 and an upward origin shift. The core overload rejects empty target sets, a Mob below minimum build height, or unavailable `canUpdatePath`. It can reuse an unfinished current Path when the requested targets contain the cached target; that return does not imply a fresh search. A new PathNavigationRegion spans the Mob block position (possibly above) plus/minus `int(followRange + regionOffset)`, and Finder receives follow range, target accuracy and visited multiplier separately.

One overload needs special care: the exact `createPath(BlockPos, int, int)` body forwards `(targets, 8, false, secondArgument, (float)thirdArgument)` to `(Set, int, boolean, int, float)`. Thus the second argument becomes accuracy and the third becomes follow range; the local-variable name `pRegionOffset` does not change that bytecode behavior. Preserve the actual descriptor/call, rather than inferring semantics from parameter names or changing upstream Minecraft.

A new non-null returned Path with a target updates cached `targetPos`, `reachRange` and stuck timeout state. The core creation method does not assign Navigation's current `path`. `moveTo(Path, speed)` performs that adoption decision separately: null clears the current Path and returns false; coordinate-equal `Path.sameAs` retains the existing object; an already-done path or zero nodes returns false after the relevant checks/trimming. Otherwise it records speed and stuck-check position/tick and returns true. Coordinate equality compares node count and XYZ only, not target, reached flag, costs, reference identity or next-node index. A true return can therefore retain an older Path/index and does not establish destination arrival.

`recomputePath` permits an immediate recomputation only when `gameTime - timeLastRecompute > 20`, not `>=20`. With a non-null target it clears the old Path, creates a replacement and updates time/flag. Within the interval it sets delayed recomputation; normal tick attempts it again. The eligible-but-null-target branch does not update the time/flag. `shouldRecomputePath` is another predicate: it refuses when recomputation is pending, requires an unfinished nonempty Path, then compares a changed block to the midpoint of Mob/end-node using remaining node count as the proximity radius. A predicate result is not a completed recompute.

Base tick increments its navigation tick, handles delayed recompute, follows/advances the selected path, and sends the next node's entity-adjusted position to MoveControl with ground-Y correction. A navigation request remains distinct from actual sampled motion. Base `stop()` clears the Path; it does not by itself erase all MoveControl/Boss/custom movement state.

## Waypoints, collision and stuck handling

Waypoint XZ tolerance is `width/2` when width>0.75, otherwise `0.75-width/2`; Y tolerance is less than1. Follow-path can advance by proximity or allowed directional corner cutting. Base corner cutting excludes DANGER_FIRE, DANGER_OTHER and WALKABLE_DOOR. The directional test also checks the next/subsequent-node geometry and an overshoot dot product. `Path.getEntityPosAtNode` applies `int(width+1)*0.5` to X/Z; do not substitute that position for a sampled Mob observation.

The base `canMoveDirectly` returns false, and this Ground subclass does not override it. Do not attribute an older-version ground DDA shortcut to this artifact. Flying/water/amphibious direct checks call a single `COLLIDER` ray to the end plus half Mob height, with `ANY` or `NONE` fluid policy. That ray is not a swept full bounding-box collision proof. Walk accepted-node processing uses different floor-shape and AABB checks described below.

Stuck position checks occur after more than100 navigation ticks. The distance threshold is `speed * 100 * 0.25` for speed>=1 and `speed² * 100 * 0.25` otherwise, compared as squared distance. A failed check marks stuck and stops the Path. The per-waypoint timeout accumulates game-time deltas for a repeated next node, computes distance/speed*20 for a new node with positive speed, and stops after greater than3 times that limit. `resetStuckTimeout` resets node/timer/limit/stuck, not `lastTimeoutCheck`. Ground trim first applies base cauldron-node elevation, then optionally truncates at the first sun-exposed node. These mechanisms are not equivalent to target reachability or observed movement success.

Ground's float-water surface scan has a16-block bailout; Walk's start-node scan and Fly's start scan are separate bodies with different stopping conditions. Record the executing owner/method rather than assigning one limit to the entire family.

## Search lifecycle

The public `PathFinder.findPath(region, mob, targets, maxDistance, targetAccuracy, searchDepthMultiplier)` clears its heap, prepares its evaluator for the actual region/Mob, obtains the start node, resolves target nodes, executes the internal search, and calls evaluator `done()` before returning a non-null-start search result.

The internal search initializes start g=0, h from the nearest target heuristic, and f=h. Its integer visited limit is the float product `maxVisitedNodes * searchDepthMultiplier` converted to int. It increments its visit counter and checks the limit **before** popping a new node: a converted limit of1 allows no pop. A recorder must not silently change this budget or loop order. The public method has no `finally`: a null start returns without `done()`, and an exception does not guarantee cleanup.

Popped nodes are marked `closed`. Manhattan distance <= target accuracy marks a target reached, and finding any reached target ends expansion. Otherwise expansion requires the current node's Euclidean distance from start to be less than max range. The neighbor edge uses the original virtual Finder `distance` (base Euclidean, Warden override XZ). It writes `neighbor.walkedDistance = current.walkedDistance + edge` before the acceptance comparison, computes tentative g=current.g+edge+neighbor.costMalus, and accepts only walkedDistance<max range plus absent-from-open or improved g. Accepted improvements set `cameFrom`, g and h=`nearest target distance * 1.5`, then change heap cost or set f/insert. Start h is unweighted. The Finder itself does not supply a universal closed-node filter; evaluator neighbor rules matter.

These are actual algorithm fields, not proof that every cached candidate was accepted. A changed walkedDistance can belong to a rejected relaxation; cached g/cameFrom can describe an earlier accepted state. The weighted heuristic and special edge distance do not establish a globally minimum-cost route.

`getBestH` updates each Target's closest `bestNode` only when its heuristic improves. Reconstruction walks `cameFrom` to build the node list. Reached target candidates are compared by node count; when no target is reached, fallback candidates are compared by Path distance-to-target, then node count. Path's stored distance-to-target is final-node Manhattan distance at construction; later trim/replace does not recompute that final field. A non-null partial Path with `canReach=false` is not a complete path to the destination, and `canReach=true` is a search result within accuracy, not actor arrival.

## Search structures and evaluator lifetime

| Structure | Actual state and interpretation |
|---|---|
| `Node` | XYZ, packed hash, heapIdx, g/h/f, cameFrom, closed, walkedDistance, costMalus and type. Defaults include heapIdx=-1 and type=BLOCKED. `inOpenSet` tests heapIdx>=0; it does not inspect a heap. `cloneAndMove` copies algorithm fields/reference, so a trimmed clone is not a new search evaluation. |
| `Target` | Extends Node, adds bestHeuristic/bestNode and reached. Strictly improved heuristic changes bestNode; reached and closest-so-far are separate. |
| `BinaryHeap` | Orders by f, tracks node heapIdx, grows its128-entry backing array, refuses inserting an already-indexed node, and clears a popped node's heapIdx. `changeCost` writes f and reorders; ties do not provide a total stable identity ordering. `clear()` changes size only, without clearing every old node's index. A cached field is therefore not universal lifetime proof. |
| `Path` | Mutable node list and nextNodeIndex, final target/distToTarget/reached, optional debug open/closed/target arrays. `isDone` is index>=node count. `sameAs` is coordinate-only. Streamed Node debug fields include walkedDistance/costMalus/closed/type/f, not the full g/h/cameFrom graph. |
| `NodeEvaluator` | `prepare` stores region/Mob, clears cached nodes and sets integer extents `floor(width+1)`, `floor(height+1)`, `floor(width+1)`. `done` nulls region/Mob, but does not clear the node cache. The next prepare clears it. Packed `Node.createHash` keys are not a global collision-free identity; retain scoped reference IDs separately. |

The Finder's fixed neighbor array has32 slots; family evaluators emit different subsets. Exact selection/run/process/Arena/search/reference boundaries must accompany observations. Persistent cached references after cleanup do not establish their validity for a later search.

## Evaluator families and accepted nodes

All6 exact NodeEvaluator-family owners are included below. `getBlockPathType` describes classification; `findAcceptedNode`, `getNeighbors` and Finder relaxation apply additional independent rules.

| Actual evaluator | Relevant rules |
|---|---|
| `NodeEvaluator` | Abstract prepare/cache/extent/door/float/fence base; it does not define a universal ground, water or air neighbor policy. |
| `WalkNodeEvaluator` | Chooses start using fluid-standing/float/ground/falling branches, tries bounding-box corners if needed, but still returns a fallback center start when no candidate passes. Classifies the integer extent volume. Emits4 horizontal cardinal plus up to4 diagonals, with step/floor/fall/fluid/collision rules. A cardinal neighbor requires non-null/not-closed and `(neighbor.costMalus>=0 || current.costMalus<0)`, so negative cost is not an unconditional rule for every edge/start. Diagonals require supporting nodes, no upward side nodes/WALKABLE_DOOR, nonnegative diagonal and side constraints, with a narrow-Mob two-fence exception. |
| `FlyNodeEvaluator` | Extends Walk but uses up to26 neighbors in3D, with side/intermediate-node nonnegative constraints on diagonals. A node must pass effective malus>=0 before creation; `isOpen` additionally requires not-closed. WALKABLE acceptance adds1 to cached cost after max(existing,effective), potentially repeatedly. Start candidates are four corners for larger bodies or up to10 random positions within a1.5-inflated small-body box. `prepare`/`done` call Walk and also invoke the Mob start/done callbacks themselves: base callback dispatch can occur twice. Do not replay these methods for observation. |
| `SwimNodeEvaluator` | Emits6 axial plus4 horizontal diagonals. Accepts WATER or allowed BREACH with nonnegative effective malus. Empty fluid adds8 after max(existing,effective), potentially repeatedly. Volume scanning can return BREACH immediately on an air/pathfindable-water cell; that early return is not an all-remaining-cells collision proof. Normal nodes must not be closed; diagonal side nodes need nonnegative cost but need not themselves be open. |
| `AmphibiousNodeEvaluator` | Extends Walk, adds up/down WATER neighbors (downward excluded from TRAPDOOR), and marks WATER beside any raw BLOCKED neighbor as WATER_BORDER. Prepare calls WATER=0, temporarily saves effective WALKABLE/WATER_BORDER and sets6/4; done restores those two numeric values, then Walk cleanup. These bodies do not restore WATER. When shallow preference is enabled, each emitted WATER neighbor below sea level−10 adds1, potentially repeatedly. |
| `Frog$FrogNodeEvaluator` | Amphibious subclass: underwater start uses floor bounding-box minY, without base Amphibious +0.5. A position above `FROG_PREFER_JUMP_TO` classifies as OPEN; otherwise it delegates. Its Navigation enables shallow preference. |

Walk's `findAcceptedNode` rejects floor rise greater than `max(1.125, stepHeight)`, classifies with the selected Mob/evaluator and initializes nonnegative candidates via max(existing,effective cost). A partial-collision *current* type (fence/closed door) can trigger swept sampled AABB checks toward the candidate. Step-up recursion observes its remaining vertical limit and excludes unpassable rail/trapdoor/powder snow and non-walkable fence unless permitted; narrow bodies also undergo a step clearance AABB test. OPEN descent stops at build/fall limits or an impassable type; water descent depends on non-amphibious/non-float conditions. A blocked sentinel can be returned with cost−1; a partial-collision sentinel can be marked closed. Being returned/cached is not being emitted as a neighbor or accepted by Finder.

Floor height comes from the block below's collision-shape top; floating/amphibious water uses Y+0.5. Collision results are cached `!region.noCollision(mob, AABB)`, independently of default malus. Walk cleanup clears type/collision caches and invokes Mob cleanup; custom callbacks/virtual setters/getters can affect the runtime outcome. The static bodies establish their calls and defaults, not all custom execution branches.

## Capture boundary

The evaluator's cached nodes belong to a particular search. Capture must occur before evaluator cleanup invalidates the relevant state, and preserve search identity. The internal search return is a candidate observation point; the outer public return occurs after `done()`.

The inspected normal PathFinder body does not call `Path.setDebug()`. `Path.getOpenSet()` and `getClosedSet()` merely return optional debug arrays. Their absence is not an empty actual search frontier or proof no nodes were visited.

An armed recorder can observe existing original invocations and copy a bounded number of node fields at a proven hook. It must distinguish actual open membership, closed nodes, cached/initialized candidates and unestablished evaluation. It must not invoke a second search, advance the evaluator, or reconstruct missing nodes and call them captured.

The explicit [original heap-operation channel](PATH-HEAP-OPERATION-RETURN-2026-10-04.md) adds start/accepted insertion, cost-update and popped-before-caller-close boundaries with finite per-search reference identities. It preserves original virtual dispatch and does not claim a complete open/closed lifecycle or infer rejection/final cost from a capped stream. Native acceptance is recorded separately from source verification.

## Terrain and effective type malus

`BlockPathTypes` carries a default type malus. `Mob.getPathfindingMalus(type)` can read a controlled vehicle Mob's malus map when that vehicle permits passengers to inherit malus. Otherwise it reads the selected Mob's override map, falling back to the type default. A naive selected-Mob-only override table is incomplete.

WalkNodeEvaluator also uses entity extent, door/float/fence settings, terrain/hazard classification and collision tests. A queried regional type value is not necessarily the costMalus used by an accepted node.

[Terrain classification and malus semantics](TERRAIN-MALUS-SEMANTICS-2026-10-05.md) records all25 declared default values, Forge callback precedence, hazards, doors/rails and actual Mob override examples. Defaults, getter returns, evaluator adjustments and relaxed-node costs are separate evidence categories.

An explicit bounded ground field must distinguish:

1. observed block/terrain input;
2. static ground `getBlockPathTypeStatic` query result;
3. default type malus;
4. effective `Mob.getPathfindingMalus` getter result and inherited/override provenance where exposed;
5. actual recorded evaluated-node `costMalus`;
6. cells merely queried by the observer.

Static terrain classification is not full Mob-specific node acceptance. Fly/swim/amphibious evaluators have separate semantics; never label a ground query as the selected aquatic/aerial evaluator. Negative costs/blocked categories and numeric values need text/pattern encoding in addition to color.

## Navigation and execution

Ground, flying, water-bound, wall-climbing and amphibious/special evaluator families must remain distinct. PathNavigation's current Path, node index, target and reachability are sampled selected state. The sampled actual Motion Trace remains independent, allowing diagnosis of selected-route versus execution differences.

Regional queries must be explicitly requested, volume/radius bounded, and refuse unavailable chunks rather than loading/scanning the world. Search bursts need independent size/time budgets and measured observer cost. Existing scoped native path/malus records remain valid in their documented windows; the static R64 research adds no new native acceptance. Full combined diagnosis and observer-cost acceptance remain pending in the [original requirement reconciliation](ORIGINAL-REQUIREMENT-RECONCILIATION-2026-10-05.md).

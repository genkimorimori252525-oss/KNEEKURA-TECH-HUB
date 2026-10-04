# Pathfinding and malus — Minecraft 1.20.1 ANCHOR

Evidence: PathNavigation families, PathFinder, NodeEvaluator families, Path, Node, Target, BinaryHeap, BlockPathTypes and Mob in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

## Search lifecycle

The public `PathFinder.findPath(region, mob, targets, maxDistance, targetAccuracy, searchDepthMultiplier)` clears its heap, prepares its evaluator for the actual region/Mob, obtains the start node, resolves target nodes, executes the internal search, and calls evaluator `done()` before returning a non-null-start search result.

The internal search initializes start g=0, h from the nearest target heuristic, and f=h. Its integer visited limit is the float product `maxVisitedNodes * searchDepthMultiplier` converted to int. It increments its visit counter and checks the limit **before** popping a new node. A recorder must not silently change this budget or loop order.

Popped nodes are marked `closed`. Neighbor relaxation computes tentative g from current g + neighbor distance + the neighbor's actual `costMalus`; accepted improvements set `cameFrom`, g, weighted h, and update/insert heap cost. These are actual algorithm fields, not a proof that every cached candidate was accepted.

Target reachability, target accuracy, the distance limit, visited budget and path reconstruction influence the result. A selected Path with `canReach=false` is not equivalent to a proven complete path to the exact destination.

## Capture boundary

The evaluator's cached nodes belong to a particular search. Capture must occur before evaluator cleanup invalidates the relevant state, and preserve search identity. The internal search return is a candidate observation point; the outer public return occurs after `done()`.

The inspected normal PathFinder body does not call `Path.setDebug()`. `Path.getOpenSet()` and `getClosedSet()` merely return optional debug arrays. Their absence is not an empty actual search frontier or proof no nodes were visited.

An armed recorder can observe existing original invocations and copy a bounded number of node fields at a proven hook. It must distinguish actual open membership, closed nodes, cached/initialized candidates and unestablished evaluation. It must not invoke a second search, advance the evaluator, or reconstruct missing nodes and call them captured.

## Terrain and effective type malus

`BlockPathTypes` carries a default type malus. `Mob.getPathfindingMalus(type)` can read a controlled vehicle Mob's malus map when that vehicle permits passengers to inherit malus. Otherwise it reads the selected Mob's override map, falling back to the type default. A naive selected-Mob-only override table is incomplete.

WalkNodeEvaluator also uses entity extent, door/float/fence settings, terrain/hazard classification and collision tests. A queried regional type value is not necessarily the costMalus used by an accepted node.

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

Regional queries must be explicitly requested, volume/radius bounded, and refuse unavailable chunks rather than loading/scanning the world. Search bursts need independent size/time budgets and measured observer cost. Full native search/malus acceptance remains pending.

# Burrower — 3D digging and segmented locomotion

Status: **legacy mechanism recovered; legacy normal-wave participation not established; 1.20.1 port and repair history mapped. Runtime NOT_RUN.**

## Core idea

Burrower separates three problems that ordinary ground navigation tends to conflate:

1. 3D route topology;
2. excavation needed to realize that route;
3. presentation of a long articulated body along the head's route.

## Legacy 1.7.10

Pinned source:
https://github.com/UnstoppableN/Invasion-mod/tree/644a52ddea104c206d022bef9edc135c060cba1d/src/main/java/invmod/common/entity

`EntityIMBurrower` creates `NavigatorBurrower(this, pathSource, 16, -4)`, a deep `PathCreator`, `TerrainModifier`, `TerrainDigger`, and sixteen visual body segments.

`NavigatorBurrower` keeps `prevNode / activeNode / nextNode` and evaluates a continuous pose between voxel nodes. Every body segment follows the same centerline later in time rather than solving its own route. When the head replans, the navigator can splice retained old route geometry so the tail can finish traversing it.

### Legacy callback defect

The pinned Burrower declares a `getBlockPathCost` overload using Minecraft `PathPoint`, while `IPathfindable` / `PathfinderIM` dispatch the MOD's `PathNode` signature. The uploaded 1.1.2 JAR confirms the same descriptor split.

Therefore the Burrower-specific `PathPoint` method does **not** override the custom pathfinder callback; the inherited `EntityIMLiving.getBlockPathCost(PathNode,...)` services that dispatch.

Lesson: verify the exact method descriptor before claiming a similarly named method is an active polymorphic hook.

### Legacy gameplay boundary

The source defines a `burrower` pattern and `MobBuilder` can instantiate it, but the pinned 1.1.2 wave definitions never reference that pattern: not Wave 1–11, not the >11 extended pool, and not continuous mode. The normal entity/spawn-egg registration path also does not register `EntityIMBurrower`.

So the legacy Burrower is strong **technology evidence**, not established normal 1.1.2 invasion content.

## Modern 1.20.1

Pinned source:
https://github.com/kevintrini2811/Invasion-Mod/tree/aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10/src/main/java/com/invasion/entity

### 3D successor generation

`BurrowerNavigation` adds vertical wall-surface and ledge/corner candidates. Route cost can favor enclosed/tunnel-like locations and penalize solid/non-pathfindable/configured material.

### Phase-owned ledge traversal

Modern ledge movement uses explicit phases:

```text
APPROACH -> CLIMB -> CROSS
```

A reduced climb step and collision-box clearance prevent the head from cutting through an inside corner. Replanning can preserve an in-progress climb rather than restarting it.

### Dig the collision that actually stopped motion

Modern movement compares requested displacement with realized displacement. When an axis is lost to collision, the navigator derives a block at the head-side collision boundary and requests excavation there.

When a partial/non-terminating path reaches its endpoint, Burrower can drill one cell along the dominant axis toward the intended target. A partial path becomes a tunneling frontier rather than only a failure.

### Render from actual movement history

The modern port reconstructs the body from the head's **real traveled trace**. Client history is resampled at fixed distance intervals (about 0.20 block), keeping segment spacing stable across speed changes, stalls and collision.

A bounded ring buffer replaces broad per-segment synchronized pose state. A separate unsaved tail hitbox forwards damage to the parent.

## Bounded repair history

| Commit | Observed repair theme |
|---|---|
| `a8348e0f` | major Burrower port completion |
| `23a101f4` | digging triggered from movement collision |
| `2869486e` | drilling beyond a non-reaching partial route |
| `20ebb2b6` | virtual-position / double-movement drift |
| `57d8b6b9` | waypoint orbiting and ledge corner handling |
| `d40b627f` | physically relevant excavation targeting |
| `a03aadef` | local segment reconstruction + tail hitbox |
| `9f5e2a11` | client history ring-buffer optimization |
| `3512f461` | explicit stair phases / mid-climb continuity |
| `0471d172` | revert of a path-block-avoidance change; cause not inferred |

## Reusable rules

1. Path topology and body animation should share one centerline.
2. Long bodies should follow **realized movement**, not only predicted route nodes.
3. Distance-based history sampling is more stable than tick-based samples.
4. A climb/cross transition should own movement until completion or abort.
5. Requested-vs-realized displacement is useful collision evidence for mining AI.
6. A partial path may be a productive excavation frontier.
7. Verify exact method descriptors before promoting a hook.

## KNEEKURA use

For future giant/serpentine/tunneling mobs, the modern “3D route + collision-driven mining + actual-motion breadcrumb body” design is substantially more reusable than a literal port of legacy `NavigatorBurrower`.

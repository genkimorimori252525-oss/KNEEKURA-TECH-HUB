# Liberty's Villagers — bounded failure / repair history

## Scope

This history combines:

- original public `changelog.md`;
- original 1.20.1 Architectury branch commit history;
- maintained Revived 1.20.1 source differences and release notes.

No historical bug was reproduced in-game in this pass.

## 1. Bed pathfinding and occupied beds

Original changelog shows multiple iterations:

- "Improvements for villager bed pathfinding"
- check bed occupancy before walking toward it
- later fix: villagers still go near an occupied bed when all beds are occupied
- sleep task range improved for more accurate pathfinding

Current source implements:

- occupied-bed filtering during POI acquisition;
- empty-bed-first search in WalkHome;
- fallback to ordinary occupied-bed behavior;
- Manhattan-style proximity adjustments.

**Lesson:** filtering a busy resource is not enough. Define fallback behavior for the case where all
resources are busy.

## 2. Path nodes around stairs/slabs

Current `EntityNavigationMixin` comments describe a villager on slab/stairs considering a future
node "close enough", then trying to jump to an invalid stair position.

Repair:

- calculate horizontal squared distance to the exact current path node;
- prevent premature vanilla node advancement.

**Lesson:** a global node-reach heuristic can fail on geometry where the required approach direction
matters.

## 3. Stuck villagers and fuzzy targeting

Historical changelog sequence:

- villagers stuck on each other;
- fuzzy targeting after a timeout;
- later fuzzy-target spam fixes;
- improved stuck handling;
- improved fuzzy logic and teleporting.

Current design watches movement at effective feet position and escalates after roughly three seconds.

**Lesson:** track progress independently from Navigation's own "done" state. An active path does not
prove physical progress.

## 4. Teleport as last-resort recovery

Original 1.20.1 source teleports after repeated fuzzy failures.

Revived 2.0.1 release says villager teleporting was disabled.

Current maintained source:

- `allowVillagerTeleporting=false`;
- `maxTeleportDistance=3.0`;
- teleport only after >3 fuzzy attempts and only inside the configured bound;
- otherwise reset and retry fuzzy routing.

**Lesson:** teleport recovery may solve visible stuck states but destroys spatial simulation
semantics. Make it opt-in, bounded and late in the recovery ladder.

## 5. PANIC blocked by job-site de-duplication

Current 2.0.2 source commit `f2e2548` adds a PANIC exception to
`WalkTowardJobSiteTaskMixin`.

Before:
- if WALK_TARGET already existed, job-site code was cancelled.

After:
- if Brain Activity.PANIC is active, the guard returns without cancelling.

Revived release text says this fixes "villagers not running for their life".

**Lesson:** de-duplication/anti-spam rules need an explicit authority hierarchy. Emergency actions
must be able to replace a lower-priority destination.

## 6. Path classifier context and mod compatibility

Original source used one static `lastUsedEntity` in `LandPathNodeMakerMixin`.

Maintained source uses a `ThreadLocal<MobEntity>`:

- capture at entity-aware `getNodeType(..., mob)` HEAD;
- clear at RETURN;
- static `getCommonNodeType` reads thread-local context.

Revived 2.0.1 AUTHOR_CLAIM says it fixes a crash with Mowzie's Mobs.

The exact causal link between the Mowzie crash and this specific ThreadLocal change is **INFERENCE**
unless a trace/issue is pinned, but the source change clearly removes cross-call global context.

**Lesson:** static mutable context inside path classification is unsafe around nested/concurrent
path computations and other mixins.

## 7. Golem shore range hang

Original changelog records a config rename:
`GolemsMoveToShoreRange -> GolemsPathfindToShoreRange`
because old installations could retain a very large default number and hang the game.

Current default: 10.

**Lesson:** any cubic/outward search range is a performance-critical config. Renaming/migrating
unsafe historical values may be necessary; validation/caps are preferable.

## 8. Return-to-shore needed several repairs

Historical notes include:

- Iron Golems should not chase drowned into water;
- ReturnToShoreGoal should not always run on first load;
- shore pathfinding improvements.

Current behavior:

- avoid water targets;
- search for supported dry cell;
- require actual reachable Path;
- if stalled at edge, relocate to next path node and continue.

**Lesson:** recovery Goals need explicit activation preconditions; adding a high-priority Goal can
silently take control even when no recovery is needed.

## 9. Farmer crop imitation refinement

Original changelog records that "prefer same crops" was improved: when an empty farmland has no
just-harvested crop identity, the farmer looks at surrounding crops to choose a matching seed.

Current source scans a local neighborhood for Crop/Gourd/Stem context.

**Lesson:** local imitation is robust when direct task history is unavailable.

## 10. Forge/Architectury rewrite instability

Original 1.20.1 branch history contains:

- initial Architectury commit where Fabric worked but Forge crashed;
- Forge startup fix, followed by another crash in core task creation;
- mixin crash fixes;
- Forge overlay still broken;
- later overlay fix at branch head.

**Lesson:** a large mixin-based AI patch can be behavior-correct and still fail at loader/mapping
boundaries. Loader/runtime validation is independent evidence from source logic review.

## 11. Mapping/synthetic-method fragility

Current 1.20.1 source injects into multiple Yarn synthetic names such as:

- `method_46885`
- `method_47187`
- `method_47156`
- `method_47160`

and modifies constants/invocations inside them.

**Lesson:** these are high-fragility integration points. For TECH-HUB, record the semantic contract
(e.g. "filter non-home POI search at night") separately from exact Mixin locator.

## 12. Full work-task replacement conflict surface

`VillagerTaskListProviderMixin.createWorkTasks` cancels vanilla's implementation and supplies a
replacement list.

This is effective for adding profession habits but can collide with other mods targeting the same
work bundle.

**Lesson:** when reconstructing, prefer composition/adapter injection if possible. If replacement is
required, make the ownership explicit and inventory all vanilla tasks being preserved.

## 13. Performance without benchmarks

Potential high-cost knobs:

- POI 128;
- path range 256;
- farmer volume scan;
- animal/patient scans;
- bell searches;
- golem shore 3D search.

The original history already demonstrates one real performance failure from an oversized search
range.

**Lesson:** configurable spatial radius should be treated as complexity budget, not only gameplay
preference.

## Evidence gaps

Not established:

- full issue/PR chain for every historical fix;
- exact Mowzie crash stack trace;
- runtime comparison against vanilla;
- server TPS cost for enlarged default ranges;
- exact distributed JAR SHA/source equivalence;
- behavior under major villager-overhaul mods.

Status: **PARTIAL / SOURCE+CHANGELOG BACKED**.

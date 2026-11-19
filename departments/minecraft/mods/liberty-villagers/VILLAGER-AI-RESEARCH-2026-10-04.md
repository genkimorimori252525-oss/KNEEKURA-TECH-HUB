# Liberty's Villagers — Villager AI and village habits research — 2026-10-04

## 1. Question

What does Liberty's Villagers actually improve in Minecraft villagers, and which techniques are
worth recovering for KNEEKURA?

This is a targeted source-backed study of the 1.20.1 line, with the original 2.0.0 source retained
as design baseline and the maintained Revived 2.0.2 source head used for current fixes.

Evidence language:

- **DIRECT_OBSERVATION** — visible in pinned source/diff.
- **AUTHOR_CLAIM** — release/changelog/project text.
- **INFERENCE** — engineering lesson derived from source.
- **UNKNOWN** — not established by this pass.

## 2. Architectural character

The mod keeps Minecraft's Villager Brain, MemoryModules, Activities, POIs and Schedule.

It does **not** implement a replacement planner.

Its architecture is:

```text
Vanilla Villager Brain
   |
   +-- POI search / ownership patches
   +-- walk/reach/path recovery patches
   +-- hazard/node-cost patches
   +-- WORK task bundle replacement
   +-- profession-specific custom tasks
   +-- life-policy hooks (sleep/breed/age/food)
   +-- golem/cat village-boundary policies
   +-- debug / memory / POI observability
```

This is an important distinction from Ages of Dominion. Ages centralizes work into its own RTS FSM;
Liberty's Villagers tries to make the existing vanilla villager system more coherent.

## 3. POI range becomes a configurable village-scale contract

Current defaults in `VillagerPathfindingConfig`:

- `findPOIRange = 128`
- `pathfindingMaxRange = 256`
- `minimumPOISearchDistance = 3`
- `walkTowardsTaskMaxRunTime = 2400`

These values are injected into multiple vanilla tasks rather than only one search call.

Affected surfaces include:

- `FindPointOfInterestTask`
- `WalkHomeTask`
- `VillagerWalkTowardsTask`
- `GoToWorkTask`
- `TakeJobSiteTask`
- `SleepTask`
- meeting walk task
- breeding home search
- Iron Golem scared-villager/follow range behavior

**Technique:** the village has an operational radius. Bed, job, meeting and movement code should
not each use unrelated constants if the design supports vertical/large settlements.

## 4. POI arrival is semantic, not exact-block arrival

Several bugs arise because a villager can be physically at a usable bed/workstation while the
vanilla distance metric says it is not "close enough", especially around stairs/slabs/doors.

The mod changes multiple completion tests and, in selected POI completion paths, prefers Manhattan
distance logic.

Examples:

- `ForgetCompletedPointOfInterestTaskMixin` keeps a POI memory unless dimensional mismatch or
  Manhattan distance >=4;
- `WalkHomeTaskMixin` replaces a squared-distance test with Manhattan distance and a small
  constant;
- `SleepTaskMixin`, `GoToWorkTaskMixin`, `TakeJobSiteTaskMixin` expand usable completion
  envelopes;
- `EntityNavigationMixin` uses squared horizontal distance to the current path node so an entity
  does not incorrectly skip a node on steep U-turn/stair/slab geometry.

**INFERENCE:** "reached the job" and "reached this path node" are separate contracts. The arrival
metric should match the semantic action being attempted.

## 5. Bed selection treats occupancy as world state

Two related paths are patched.

### Finding a bed

`FindPointOfInterestTaskMixin` filters bed POIs whose BedBlock `OCCUPIED` property is true.

### Walking home

`WalkHomeTaskMixin` first asks for unoccupied beds over the configurable POI range. If none exist,
it falls back to normal behavior around occupied beds.

This evolved from earlier release fixes where villagers either chose occupied beds incorrectly or
failed to go near a bed when all beds were occupied.

**Technique:** resource reservation state must be part of candidate filtering. "Nearest bed" is not
equivalent to "nearest currently usable bed".

## 6. Nighttime POI policy

`FindPointOfInterestTaskMixin` inspects time of day.

After tick 13000, if the option is enabled:

- HOME memory searches remain allowed;
- non-HOME POI acquisition is rejected for villagers.

That prevents nighttime workstation/meeting-point churn while still allowing bed acquisition.

**Technique:** schedule is more than Activity switching. Expensive/global resource discovery should
also obey phase policy.

## 7. Work behavior is a reconstructed WORK bundle

`VillagerTaskListProviderMixin.createWorkTasks` cancels vanilla's returned task list and provides a
new list.

The bundle still retains familiar vanilla pieces:

- busy follow behavior;
- trade-offer holding;
- player interaction;
- walk toward job site;
- gifts to Hero;
- `ScheduleActivityTask`.

But the main work block becomes a `RandomTask` with profession-specific work behaviors.

Priorities inside that random work group are deliberately separated:

- ordinary job-site/wandering work;
- secondary profession action;
- tertiary action.

**Boundary:** this is not a small append-only patch. It is a whole-method work-task replacement and
is therefore one of the highest compatibility-risk surfaces in the mod.

## 8. Armorer becomes a settlement maintenance role

If enabled, Armorers run `HealGolemTask`.

- scan Iron Golems in configurable range (default 32);
- filter to wounded, alive, visible, non-invulnerable targets;
- walk toward one using Brain LOOK_TARGET and WALK_TARGET memories;
- on arrival, play repair sound and heal to max.

The shared `HealTargetTask` supplies:

- patient selection;
- walk/look memory control;
- completion range;
- cleanup of memories;
- invalid-target checks;
- a bounded MultiTickTask lifetime.

**Technique:** profession-specific service behavior can be implemented as a normal Brain task that
claims the same WALK_TARGET/LOOK_TARGET resources as vanilla work.

## 9. Cleric becomes a healer

`ThrowRegenPotionAtTask` can target wounded villagers and/or players in configurable range.

It predicts a small amount of target movement, creates a regeneration splash potion and launches it
with a ballistic vertical adjustment.

The patient predicate avoids:

- full-health targets;
- dead/invisible/invulnerable targets;
- targets already carrying Regeneration.

**Technique:** role behavior should check whether its effect would be redundant before spending a
movement/action slot.

## 10. Food professions create a village resource flow

Animal-feeding behaviors are profession-specific.

Examples:

- Butcher -> chicken/cow/pig/rabbit/(optional sheep)
- Fletcher -> chicken
- Leatherworker -> cow
- Shepherd -> sheep

The villager needs the appropriate food in inventory.

Before feeding, `FeedTargetTask` counts animals in the configured area and refuses the behavior
when local population is already at or above `feedMaxAnimals` (default 30).

**Technique:** an autonomous production behavior should include a local saturation guard. Without
it, a "helpful" task becomes unbounded population growth.

## 11. Inventory is role-aware

The mod removes some generic seeds/wheat from the universal villager gatherable set, then extends
`VillagerProfession.gatherableItems` per profession.

It also patches villager-to-villager item sharing so resources move toward professions that use them.

Examples:

- Farmer receives pumpkin resources;
- animal-feeding professions receive wheat/seeds/carrots/potatoes;
- Fisherman can gather raw cod/salmon.

**Technique:** job AI and inventory acquisition must agree. Adding a new task without adding a
resource-acquisition path produces a behavior that works only when a player manually supplies it.

## 12. Fisherman becomes a real physical job

The Fisherman path is unusually complete.

### Secondary POI

`VillagerProfessionMixin` declares WATER as a secondary job-site material when fishing is enabled.

### Sensor range

`SecondaryPointsOfInterestSensorMixin` expands fisherman X/Z secondary-POI scan using
`fishermanFindWaterRange`.

### Fishing action

`GoFishingTask`:

1. refuses to fish while the villager itself is in water;
2. searches nearby still-water cells with air above;
3. refuses water above the villager;
4. computes a bobber origin;
5. rejects solid start cells;
6. raycasts bobber bottom/left/right clearance;
7. checks for living entities in the casting corridor;
8. chooses the first valid water target;
9. equips a rod and looks at the water for ~3 seconds;
10. spawns a real FishingBobberEntity;
11. waits until a catch/invalid state;
12. retracts and removes the rod.

Other work/interaction tasks explicitly suppress themselves while the villager is holding the
fishing rod.

### Workstation processing

`FisherWorkTask` runs at the barrel and converts raw cod/salmon in villager inventory into cooked
fish, dropping overflow.

Cooked fish can also be configured as villager food.

**Technique:** a convincing profession is a pipeline:
`discover workplace resource -> perform physical action -> produce inventory -> process at job site
-> exchange/use output`.

## 13. Farmer behavior models crop context

Farmer crop scanning is made configurable in horizontal and vertical planes.

The task can:

- harvest mature normal crops;
- harvest pumpkins/melons;
- plant corresponding stems;
- prefer the crop type it just harvested;
- when farmland is empty, inspect nearby crops to infer the local crop pattern;
- favor real seeds over converting harvested gourds where possible;
- compost melon/pumpkin seeds;
- make pumpkin pie from pumpkins during work.

**Technique:** local environmental context can act as a weak "custom/tradition" signal. The farmer
does not need a global field registry to make fields look coherent; it samples neighboring crops
and imitates them.

This is one of the most interesting habits in the mod for KNEEKURA.

## 14. Sleep as a life-cycle reward

If enabled, `VillagerEntity.wakeUp` heals the villager to maximum health.

This is simple, but structurally important: a daily life-cycle transition can become a recovery
checkpoint.

**Technique:** periodic life routines can have gameplay consequences without adding a new meter.
Sleep can naturally restore health, morale or fatigue.

## 15. Breeding is constrained by settlement capacity

Three independent policies exist:

- disable breeding entirely;
- require an available reachable bed (vanilla/expanded range);
- optionally also require a free acquirable workstation.

If the workstation requirement fails, both parents receive angry particles and the breeding
home-placement path is cancelled.

Baby growth duration is configurable.

**Technique:** population growth can be bound to **future productive capacity**, not only housing.
For simulation-heavy villages this prevents population expanding faster than jobs.

## 16. Nitwit and age policies are explicit rule switches

The mod can:

- turn Nitwits into unemployed villagers;
- make all villagers Nitwits;
- make all villagers babies;
- prevent babies growing;
- customize growth time.

When changing profession state to/from Nitwit, it also stops Brain tasks and releases relevant job
site POI tickets where needed.

**Technique:** changing social identity requires releasing claimed world resources and restarting
behavior, not just changing a display enum.

## 17. Path hazard policy is expressed through node costs

Villager defaults can be changed to:

- strongly avoid cactus danger;
- forbid water;
- strongly avoid water borders;
- forbid rail;
- forbid trapdoor;
- forbid powder snow;
- strongly avoid powder-snow danger;
- classify panes as blocked.

Safe fall distance is configurable (default 2), and climbing can be disabled.

For Iron Golems, a related but not identical policy is used; for example water gets positive malus
rather than exactly matching villagers.

**Technique:** danger avoidance belongs in path evaluation, not in a late "if touching cactus then
turn around" behavior.

## 18. Node typing is entity-context-sensitive

`LandPathNodeMakerMixin` changes common node classification only while evaluating Villager/Iron
Golem paths.

Current maintained source uses a `ThreadLocal<MobEntity>` captured around
`LandPathNodeMaker.getNodeType(..., mob)`.

It then treats:

- Azalea -> LEAVES;
- Stairs -> BLOCKED;
- configured PaneBlock -> BLOCKED.

The ThreadLocal replaced the original single static entity context.

**Technique:** when a static path classification helper lacks the entity parameter, context must be
scoped safely. Global mutable "last entity" is a compatibility/concurrency trap.

## 19. Stuck recovery is a staged policy

`WanderAroundTaskMixin` tracks the entity's effective feet position.

If meaningful movement has not occurred for roughly **3 seconds**:

1. ask `NoPenaltyTargeting.findTo` for a nearby fuzzy point biased toward the original target;
2. build a new path to that fuzzy point;
3. increment retry state.

After more than three fuzzy tries:

- original line: teleport toward current path/walk target;
- maintained line: teleport only if explicitly enabled **and** within `maxTeleportDistance`
  (default 3);
- otherwise reset retry state and continue fuzzy routing.

Current default:
`allowVillagerTeleporting = false`.

**Technique:** recovery should escalate from low-authority replanning to high-authority relocation.
Teleport belongs at the end of the policy ladder and should be explicit.

## 20. Walk-target anti-spam and PANIC priority

`WalkTowardJobSiteTaskMixin` normally refuses to set another walk target when a WALK_TARGET memory
already exists. This prevents repeated job-site target churn.

The maintained 2.0.2 fix adds:

`if Brain has Activity.PANIC -> do not apply this guard`.

Release note: "fix villagers not running for their life".

**Technique:** optimization/de-duplication rules must never override higher-priority emergency
behavior. Every "already have a target" guard needs an authority check.

This is one of the strongest reusable lessons in the whole mod.

## 21. Crop protection

When configured, villagers and/or golems landing on farmland call generic Block landing behavior
instead of FarmlandBlock's trampling behavior.

This preserves the physical fall reaction without executing crop-destruction semantics.

## 22. Village radius extends to guardians and cats

The nearest MEETING bell is reused as a settlement anchor.

Iron Golems can:

- keep wandering inside a configurable bell radius;
- refuse target pursuit outside that radius;
- use configurable aggro range;
- avoid water targets;
- return toward shore when stranded in water;
- respect hazard path penalties;
- have population capped.

Cats can:

- have spawn counts/range adjusted;
- remain persistent;
- stay within a bell radius;
- avoid climbing;
- alter black-cat moon/variant rules.

**Technique:** a meeting POI can serve as a lightweight territory anchor for village-associated
agents without inventing a separate town object.

## 23. Return-to-shore recovery

`ReturnToShoreGoal` searches outward within a configured cube for an air position with solid
support and no fluid, then asks Navigation for a real reachable path.

If the golem stops at a problematic water edge before finishing the path, the Goal can relocate it
to the next path node and continue.

Historical changelog records multiple iterations of this behavior.

**Boundary:** this is a targeted recovery hack, not a general-purpose water navigation system.

## 24. Brain observability is a first-class feature

`BrainMixin` can log writes to selected memories:

- WALK_TARGET
- HOME
- POTENTIAL_JOB_SITE
- JOB_SITE
- PATH

It inspects the current stack trace and tries to identify which vanilla task/sensor set the memory.

The mod also exposes tools to inspect:

- villager home;
- job site;
- meeting point;
- inventory;
- POI ownership;
- village population/job/homeless/bed/golem/cat summaries;
- manual POI enable/disable;
- reset of villager POI state.

**Technique for TECH-HUB:** when debugging Brain AI, recording **who mutated a memory and to what**
can be more valuable than only displaying the memory's current value.

This directly supports the LAB's "thought visibility" direction.

## 25. What the mod does not provide

No source evidence was found for:

- culture/reputation norms beyond vanilla gossip;
- a new social-rule planner;
- family/kinship memory;
- household ownership;
- village-wide task allocation;
- economic prices/stockpiles;
- explicit group formation;
- long-term goals beyond existing Brain/POI concepts.

The "habits" are largely profession routines and life-cycle/settlement policies layered onto
vanilla Brain.

## 26. Compatibility lessons from architecture

### Heavy mixin surface

46 mixin Java classes in the 1.20.1 source line.

Several target synthetic Yarn names such as `method_46885`, `method_47187`, etc.

**INFERENCE:** direct reuse should prefer contract reconstruction over cloning mixins wholesale.

### Full WORK task replacement

Replacing `VillagerTaskListProvider.createWorkTasks` means another mod changing the same method can
conflict semantically even if both mixins apply.

### Parameter coupling

`LivingEntityMixin` returns `findPOIRange` as GENERIC_FOLLOW_RANGE for Villagers and Iron Golems.

This makes one tuning knob influence both POI discovery and entity follow/sensing behavior.

**Recommendation for KNEEKURA reconstruction:** separate:
- POI search radius;
- target/sensor radius;
- navigation maximum range.

## 27. Performance observations

No benchmark was run.

Potentially expensive expanded operations include:

- POI queries up to 128;
- path targets up to 256;
- farmer volume scans using configurable X/Z and Y;
- animal scans up to feeding range;
- healing scans;
- bell queries;
- golem return-to-shore volume search.

Mitigations visible in source include:

- work tasks scheduled by Brain rather than every entity tick;
- first-valid fishing spot exits early because ray/entity checks are expensive;
- local saturation guards on animal feeding;
- fuzzy recovery only after stuck time;
- golem shore behavior uses chance/backoff.

## 28. Repair history distilled

Important historical failures and repairs:

- bed POI selected while occupied -> occupancy filtering and fallback;
- stairs/slab/door proximity confused arrival -> Manhattan/semantic distance fixes;
- villagers skipped path nodes on steep geometry -> node reach calculation patch;
- stuck villagers spammed fuzzy targeting -> staged retry timing;
- repeated stuck recovery teleported too aggressively -> Revived disables teleport by default and
  bounds distance;
- job-site walk-target anti-spam blocked panic escape -> Revived PANIC exception;
- old large golem shore range could hang the game -> config rename/default correction;
- static path context caused compatibility concerns -> maintained source uses ThreadLocal context;
- Architectury/Forge port initially crashed in mixins/startup -> subsequent loader-specific fixes.

## 29. Reusable KNEEKURA abstractions

### POIPolicy

```text
searchRadius
completionRadius
maxTravelRange
phasePermission(activity/time)
candidateFilter(occupied/reserved/etc.)
```

### StuckRecoveryPolicy

```text
movementWatch
 -> fuzzyTarget retry
 -> repath
 -> retry budget
 -> optional bounded relocation
```

### JobHabit

```text
profession
requiredInventory
candidateSensor
saturationGuard
move/look contract
action
outputInventory/worldEffect
```

### SettlementAnchorPolicy

```text
meetingPOI/bell
territoryRadius
wander correction
pursuit limit
spawn/population limit
```

### BrainMutationTrace

```text
entity
memory type
old/new value
caller task/sensor
tick
```

## 30. Most valuable recovered technologies

1. POI lifecycle treated as one configurable navigation system.
2. Semantic reach distance for beds/jobs.
3. Occupancy-aware bed selection.
4. Night phase gate for non-home POI searches.
5. Staged stuck recovery instead of infinite repath spam.
6. PANIC/emergency authority above walk-target deduplication.
7. Profession habit tasks inside vanilla Brain.
8. Profession-aware inventory acquisition/sharing.
9. Local crop imitation as a weak village farming custom.
10. Breeding tied to future job capacity.
11. Bell-anchored territory for golems/cats.
12. Path hazards encoded at node evaluation.
13. Memory-mutation provenance for debugging.

## 31. Primary source locators

Original design baseline:
https://github.com/gitsh01/libertyvillagers/tree/e0bade76b49a40950d69ba4ce7e5d51799e4ea7f

Maintained 1.20.1 source:
https://github.com/Leclowndu93150/Liberty-Villagers/tree/f2e25484049366fe13ec48f7c1e4d97c94809898

Key source files:

- `VillagerPathfindingConfig.java`
- `VillagersGeneralConfig.java`
- `VillagersProfessionConfig.java`
- `VillagerTaskListProviderMixin.java`
- `FindPointOfInterestTaskMixin.java`
- `WalkHomeTaskMixin.java`
- `ForgetCompletedPointOfInterestTaskMixin.java`
- `VillagerWalkTowardsTaskMixin.java`
- `WalkTowardJobSiteTaskMixin.java`
- `WanderAroundTaskMixin.java`
- `EntityNavigationMixin.java`
- `LandPathNodeMakerMixin.java`
- `VillagerEntityMixin.java`
- `VillagerProfessionMixin.java`
- `VillagerBreedTaskMixin.java`
- `FarmerVillagerTaskMixin.java`
- `GatherItemsVillagerTaskMixin.java`
- `HealTargetTask.java`
- `GoFishingTask.java`
- `ReturnToShoreGoal.java`
- `BrainMixin.java`

# Goofy Critters — bounded movement failure / repair history

## Scope

This review is source-history-backed and focuses on locomotion.

The public repository has almost no descriptive issue trail, and the only public CurseForge 1.0.0
file has no detailed release changelog. Therefore commit diffs are stronger evidence than commit
titles such as "fix".

No historical bug was reproduced in-game.

## Evidence tracks

- distributed binary: CurseForge file `7553632`
- release-era source candidate: `9188e5175828154bdae309dd352e16e338dc8089`
- post-release frontier: `96d01a7b7ceaa18c51ae0cb1e7dfac0c3d467956`

Do not attribute post-release fixes to the distributed binary.

## 1. Core Gestalt anchor locomotion predates the later reworks

The release-era candidate already contains:

- zero-speed/no-gravity Gestalt;
- empty default Goal set;
- GestaltController;
- independent GestaltHand entities;
- target-biased hand extension;
- per-hand body impulses;
- rider target projection;
- owner/wild-player following;
- procedural arm rendering.

The core locomotion concept is therefore stable across release-era candidate and frontier source.

Binary equivalence remains **UNKNOWN**.

## 2. Autonomous Gestalt follow was added by release day

Commit `9188e5175828154bdae309dd352e16e338dc8089` adds:

- owner-follow target when >=6 blocks away;
- nearest-player target for untamed Gestalt when >=6;
- fixes a procedural-arm lighting position.

This shows the same actuator system was intentionally reused for both rider control and autonomous
movement.

## 3. Flying waypoint completion was repeatedly adjusted

Commits around 2026-02-24:

- `812091d` changes flying Y threshold comparison;
- `8a35e6d` temporarily removes Y from a flying node-reach test;
- later full NoSpin implementation restores medium-appropriate Y checking.

**Lesson:** waypoint completion is not trivial for 3D movers. A strict all-axis sphere/cube check
can make an entity circle a node; ignoring Y entirely can advance too early.

Treat node completion as a locomotion-specific policy.

## 4. Ground node completion also changed

`d99e2cc` introduces configurable `distanceModifier` into NoSpinGround navigation.

`9f65e6d` later changes its node reach check again.

Frontier settles on:

- X/Z threshold based on modifier;
- Y tolerance <1 block for ground;
- tighter mode-specific logic for flying/water.

**Lesson:** entity width, medium and elevation transition all affect when a path node is considered
consumed.

## 5. Simple flying corner-cut was replaced by whole-AABB sweep

Commit `4bf75aab01d64ff0c32d31dc1a12e5aa0bc0e568` is the largest movement repair in the history.

Before:
- simple next-node/direction logic.

After:
- patched Flying PathFinder;
- entity-width-centered Path positions;
- full AABB voxel sweep;
- path type/malus validation;
- hazard checks;
- farthest valid same-elevation shortcut.

**Lesson:** point visibility is not a sufficient shortcut test for nontrivial entity dimensions.

## 6. Body/head rotation required multiple corrections

`5225cd8` replaces custom rotlerp calls with vanilla `Mth.rotateIfNecessary`.

`f68594e` corrects which side should rotate when the head moves/stabilizes.

**Lesson:** locomotion orientation has at least three independent angles:

- navigation/body;
- head/look;
- model presentation.

Trying to force all three through one interpolation rule produces visible fighting/snapping.

## 7. Airborne default state was corrected

Commit `6ab5a74` changes a flying-animal synchronized `IS_FLYING` default from false to true.

**Lesson:** movement mode state must agree with the installed MoveControl/Navigation immediately on
spawn. A transient mismatch can run the wrong controller even if the final behavior is correct.

## 8. July mass rework centralizes movement configuration

Commit `29545d7` plus frontier rework `96d01a7` reorganize the shared movement layer.

Changes include:

- consolidated `AbstractAnimatableAnimal`;
- `MobClassification` LAND/AIR/WATER;
- `MovementData`;
- dedicated ground/fly/swim controls;
- runtime control/navigation swapping;
- shared NoSpin navigators;
- revised animation/rotation control.

**Lesson:** after several species/movement modes exist, method-per-parameter overrides become hard to
maintain. Put locomotion tuning into a coherent data object while keeping algorithms shared.

This is FRONTIER evolution, not a proven January release behavior.

## 9. NoSpin does not replace A*

Current NoSpin variants still ask vanilla PathFinder / NodeEvaluator for a path.

The custom algorithm is in path following and shortcut validation.

**Lesson:** distinguish:

- route search;
- route smoothing/shortcutting;
- actuator/MoveControl behavior.

A movement system can feel radically different without replacing A*.

## 10. Gestalt has no failure-recovery planner

Gestalt has support invalidation per hand, but no global:

- "no anchors available";
- "not making progress";
- "target unreachable";
- "stuck in open void"

state machine.

**INFERENCE:** an improved reconstruction should add locomotion health metrics while preserving the
emergent anchor movement.

Candidates:

- recent displacement window;
- successful anchor acquisition rate;
- net force magnitude;
- anchor angular diversity;
- repeated target timeout.

## 11. Anchor attachment is intentionally strict

Current Controller accepts only full collision-shape blocks.

This avoids ambiguous contact points but excludes many Minecraft geometries.

Potential improvement contract:

`AnchorSurfacePolicy(worldHit, collisionShape, normal, requiredArea)`

instead of hard-coded "full block only".

## 12. Anchor force has an unexplained precision gate

Current Hand source only applies force inside an additional `length > dist` condition where:

- `length` is vector length as double;
- `dist` is `distanceTo(owner)` as float.

Both represent nearly the same center separation.

No commit message/comment explains the requirement.

Status: **UNKNOWN**.

Do not preserve it as a design requirement.

## 13. Detached helper entities carry cost

Each hand:

- ticks;
- synchronizes fields;
- persists owner/target state;
- has large client tracking range;
- renders at arbitrary distance/no culling.

This is a reasonable spectacle budget for a rare creature, but it is not automatically scalable.

Potential improvement:
- keep gameplay-significant anchors server-side;
- represent stable anchors with compact records instead of full entities where interaction is not
  needed;
- batch visual limb state.

No benchmark exists, so this remains a design option, not a measured requirement.

## 14. Owner lookup is compatibility-sensitive

Hand owner resolution calls a reflective obfuscated Level method through `GoofyUtil`.

This is a source-level fragility, not a core locomotion requirement.

Preserve:
- stable owner identity.

Do not preserve:
- private reflective lookup mechanism.

## 15. Procedural rendering is powerful but unbounded by total span

Each hand renderer fills the body-to-hand distance with repeated arm segments.

Render work therefore scales with total anchor span.

Potential improvements:

- maximum visual segment count;
- distance-based segment LOD;
- far-view spline/line representation;
- culling based on body and anchor visibility.

No performance data was found.

## 16. Repository end state

The repository is archived/read-only after July 2026.

No automated tests were found.

No matching public GitHub issue history for movement/Gestalt was found in the bounded search.

Therefore final status is:

**PARTIAL / SOURCE-HISTORY-BACKED / RUNTIME_NOT_VERIFIED**.

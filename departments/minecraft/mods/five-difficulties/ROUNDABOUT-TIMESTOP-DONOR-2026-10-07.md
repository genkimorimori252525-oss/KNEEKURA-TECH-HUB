# Five Difficulties X1 Preservation Port — Roundabout Time Stop donor analysis

Date: 2026-10-07

Scope: private preservation/reconstruction project. Public redistribution is out of scope.

Candidate donor:
- Hydraheads/RoundaboutMod
- inspected commit: `fd4cd74729337081269d20d1b7b57334c95879e9`
- Minecraft 1.20.1 implementation line
- Roundabout license v1.2 permits copying/modifying/reusing with author credit; even for this private project, provenance should be preserved in source comments/docs.

Decision: **USE ROUNDABOUT AS THE TIME-STOP ENGINE DONOR, NOT AS THE SAKUYA BEHAVIOR SPECIFICATION.**

The behavioral oracle remains Five Difficulties X1.

## Why this is a better base than the legacy Sakuya implementation

The old Five Difficulties time-stop system was recovered as a snapshot/restore style design:
- remember position/rotation/motion/tick-like state;
- repeatedly restore/freeze those values while time is stopped.

That can reproduce visible immobility, but on Minecraft 1.20.1 it fights:
- modern entity tick internals;
- client interpolation;
- AI/navigation;
- modded entity state;
- network corrections.

Roundabout instead stops the underlying update paths.

Its core model is:

`Level has active time stoppers`
→ `position/range query`
→ `CanTimeStopEntity(entity)`
→ `cancel or substitute that entity/world tick`.

That is a much stronger 1.20.1 foundation.

## Roundabout core recovered

### TimeStop interface / Level state

`event/powers/TimeStop.java` defines:
- active stopping entities;
- client-side TimeStopInstance copies;
- range tests for positions/entities;
- `CanTimeStopEntity`;
- add/remove stopper;
- client synchronization;
- block-entity interaction sync;
- ticking active stops.

`mixin/time_stop/TimeStopWorld.java` implements this on `Level`.

The server stores an immutable list of active stopping LivingEntities.

The client stores `TimeStopInstance`:
- source entity id;
- x/y/z;
- range;
- duration;
- maxDuration;
- interpolation state.

This is a useful generic contract for Sakuya.

### Server entity tick cancellation

`mixin/WorldTickServer.java` injects into:
- `ServerLevel.tickNonPassenger`;
- `ServerLevel.tickPassenger`.

If `CanTimeStopEntity(entity)` is true:
- normal entity tick is cancelled;
- LivingEntity hurt/invulnerability timers are specially managed;
- ItemEntity pickup delay can still advance;
- FishingHook and Boat receive selected substitute maintenance;
- passengers are handled deliberately.

This is superior to moving an entity back after it has already ticked.

### Block / fluid / chunk suspension

Roundabout injects into:
- block scheduled tick;
- fluid scheduled tick;
- chunk tick;
- block-entity tick eligibility.

Inside stopped range it can:
- cancel/reschedule block tick;
- cancel/reschedule fluid tick;
- cancel chunk tick work;
- suppress BlockEntity ticking unless explicitly interacted/unfrozen.

This is **optional for Sakuya**. It must be enabled only if the X1 oracle shows equivalent behavior.

### Projectiles created in stopped time

`mixin/time_stop/TimeStopProjectile.java` marks a projectile as time-stop-created when its owner can act inside stopped time.

`TimeStopThrowableProjectile` and similar projectile mixins replace normal projectile tick with:

`TimeMovingProjectile.tick(projectile)`.

`TimeMovingProjectile`:
- applies a speed multiplier;
- performs block/entity collision probes;
- slows further when approaching an entity;
- uses multipliers such as 0.7 / 0.6 for proximity slowdown;
- decays speed multiplier by 0.87 per tick;
- stops at a block/entity;
- clears the special moving-in-stopped-time state after stopping.

This creates the classic JoJo behavior:

`throw during stopped time → projectile advances/slows → hangs in space → time resumes`.

For Sakuya this is especially valuable for knives.

### Particles

`TimeStopParticleEngine`:
- marks particles created during a time stop;
- freezes pre-existing particles in stopped range;
- lets particles created during stopped time continue;
- fixes render interpolation for frozen particles.

This can be adapted, but should not automatically be enabled if X1 did not visually freeze particles.

### Animated textures

`TimeStopTextureManager` cancels TextureManager ticking while the local player is inside stopped time.

Effect:
- animated fire/water/etc can freeze on one frame.

This is a strong JoJo visual effect but is **not automatically part of Five Difficulties fidelity**.

### Damage release

`WorldTickServer` also supports Roundabout's stored time-stop damage:
- damage/momentum can be accumulated while victim is frozen;
- once victim is no longer stopped, stored damage is applied;
- stored attacker and delta buildup are cleared.

This is a JoJo/The World policy.

Do **not** inherit it by default for Sakuya.

Use it only if X1 runtime shows delayed damage with equivalent semantics.

## JoJo-specific code to remove

Do not transplant:
- StandUser;
- TWAndSPSharedPowers;
- stand XP/level;
- stand cooldowns;
- StandEntity/followers;
- Anubis possession;
- command-disc possession;
- Warden special lore rule;
- Go Beyond / Step Rule exemptions;
- stand damage reduction;
- JoJo time-stop sounds/voice;
- timestop action cooldown formulas;
- stored Stand damage policy unless X1 demands it;
- stand-specific HUD/config.

Replace these with neutral Five Difficulties interfaces.

## Proposed Five Difficulties architecture

### SakuyaTimeStopService

Per ServerLevel:

- active `SakuyaTimeStopInstance` list;
- add/remove source;
- duration;
- center/range;
- source UUID/entity id;
- flags defining what categories are frozen.

Suggested flags:

- `freezeLivingEntities`
- `freezeExistingProjectiles`
- `specialMoveNewProjectiles`
- `freezeItemEntities`
- `freezeBlockTicks`
- `freezeFluidTicks`
- `freezeBlockEntities`
- `freezeRandomChunkTicks`
- `freezeParticles`
- `freezeAnimatedTextures`
- `freezeWorldDayTime`
- `delayDamageUntilResume`

Do not decide these from Roundabout defaults.

Resolve them against X1 observation.

### TimeStopEligibility

One method:

`shouldFreeze(Entity entity, SakuyaTimeStopInstance stop)`

Categories:
- source player/Sakuya: never freeze;
- projectiles created by source during stop: use Sakuya projectile policy;
- existing projectiles: freeze or continue based on X1;
- other players: X1-defined multiplayer rule;
- mobs: freeze;
- Five Difficulties spell/projectile entities: explicit policy;
- bosses/immune entities: only if X1 has such exceptions.

No Stand knowledge.

### SakuyaStoppedProjectile

Use Roundabout's TimeMovingProjectile concept, not necessarily its exact constants.

State:
- createdDuringTimeStop;
- stored original velocity;
- current stop-motion multiplier;
- optional arm/release state;
- source TimeStop id.

Possible X1 fidelity modes:

1. `ROUNDABOUT_DECELERATE`
   - knife moves and slows toward a stop.

2. `PLACE_AND_HOLD`
   - knife is spawned/positioned and remains fixed immediately.

3. `LEGACY_X1`
   - exact behavior measured from Five Difficulties runtime.

The third is the acceptance target.

### Resume

On time resume:
- all special held knives/projectiles resume their stored/intended velocity simultaneously;
- frozen normal entities return to ordinary tick;
- frozen block/particle policies return to ordinary update;
- no JoJo Stand cooldown logic;
- no delayed damage unless X1 requires it.

This gives the desired Sakuya visual:

`time stop → player moves/places knives → world remains fixed → resume → knives/world continue`.

## Mixin strategy

For high-fidelity time stop, Mixin is justified.

Forge events alone are not sufficient to cleanly prevent every vanilla:
- entity tick;
- passenger tick;
- scheduled block/fluid tick;
- chunk/random tick;
- renderer interpolation.

Start with the smallest Roundabout-derived interception set:

P0:
- ServerLevel tickNonPassenger;
- ServerLevel tickPassenger;
- projectile tick substitution;
- client entity interpolation freeze.

Add only after X1 evidence:

P1:
- block/fluid tick;
- BlockEntity;
- particle interpolation;
- texture animation;
- chunk/random tick.

This avoids making Sakuya's power broader than the original.

## Important difference from copying Roundabout whole

Roundabout's `CanTimeStopEntity` mixes engine policy and JoJo lore exceptions.

Five Difficulties should split these:

`isInsideTimeStop`
`isExemptBySource`
`freezePolicyForCategory`
`projectilePolicy`

That makes future mod compatibility easier.

## Compatibility value

Roundabout demonstrates fixes for many 1.20.1 edge cases:
- passengers;
- boats;
- fishing hooks;
- item pickup delay;
- TNT;
- End Crystals;
- Slime collision attacks;
- Guardian attacks;
- Raid progression;
- BlockEntity interpolation;
- particle interpolation;
- animated textures;
- client camera/hurt bobbing.

These are valuable as a **bug checklist** even when their exact code is not transplanted.

For Five Difficulties, maintain:

`ROUNDABOUT_EDGE-CASE_CHECKLIST.md`

and mark each case:
- REQUIRED_BY_X1;
- NICE_TO_HAVE;
- EXCLUDED_TO_PRESERVE_X1;
- UNTESTED.

## X1 runtime oracle required before final policy

Record Five Difficulties 1.7.10 behavior for Sakuya clock:

1. existing arrow in flight before stop;
2. knife thrown after stop begins;
3. dropped ItemEntity;
4. falling sand/TNT;
5. mob AI/cooldown;
6. fire/lava/water update;
7. furnace/chest animation;
8. redstone;
9. particles already alive;
10. particles spawned by Sakuya during stop;
11. day/night clock;
12. potion/fire timers;
13. incoming/outgoing damage;
14. second player in multiplayer;
15. spell-card/danmaku entities;
16. resume tick — exact projectile velocity and synchronized release.

Each result decides one service flag.

## Donor priority

### Primary donor — Roundabout

Use for:
- Level time-stop registry;
- range/query model;
- tick cancellation shape;
- client synchronization concept;
- projectile-created-during-stop marker;
- stopped-time projectile substitute tick;
- edge-case inventory.

### Secondary reference — Time Stop Clock

Time Stop Clock has a maintained 1.20.1 Forge version and supports:
- whole-world freeze;
- local Time Box regions;
- separate freeze of entities/blocks/particles;
- whitelist;
- virtual tickrate/bullet-time modes.

It is useful as a second compatibility reference if Roundabout's Mixin approach collides with another MOD.

Do not combine both implementations blindly.

## Recommendation

Adopt this rule:

**Roundabout supplies the modern 1.20.1 time-stop machinery. Five Difficulties X1 supplies every player-visible rule.**

This is preferable to directly porting the legacy clock snapshot/restore engine.

Expected benefits:
- fewer interpolation/network fights;
- better multiplayer behavior;
- cleaner projectile freeze/release;
- much more complete 1.20.1 edge-case coverage;
- easier future compatibility testing.

The transplant should remain a self-contained subsystem so that all JoJo references can be removed and the remainder can be tested independently as `SakuyaTimeStopService`.

## Provenance

Roundabout inspected source:
https://github.com/Hydraheads/RoundaboutMod

Key files:
- `event/powers/TimeStop.java`
- `event/TimeStopInstance.java`
- `mixin/time_stop/TimeStopWorld.java`
- `mixin/WorldTickServer.java`
- `mixin/time_stop/TimeStopProjectile.java`
- `mixin/time_stop/TimeStopThrowableProjectile.java`
- `entity/TimeMovingProjectile.java`
- `mixin/time_stop/TimeStopParticleEngine.java`
- `mixin/time_stop/TimeStopTextureManager.java`
- `stand/powers/presets/TWAndSPSharedPowers.java`

Inspected commit:
`fd4cd74729337081269d20d1b7b57334c95879e9`.

Roundabout LICENSE v1.2 permits reuse/modification and asks that original authorship be respected/credited.

Secondary current references:
- Roundabout 1.20.1 Forge release line: CurseForge
- Time Stop Clock 1.20.1 Forge: CurseForge / Suel-ki/TimeStopClock

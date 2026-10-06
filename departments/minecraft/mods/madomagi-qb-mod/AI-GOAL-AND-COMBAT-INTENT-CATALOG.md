# QB-MOD / Garnet-MOD 1.6.4.082 — AI Goal / combat-intent catalog

Date: 2026-10-07

Primary evidence:
- QB-MOD SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

Purpose: capture the **tactical layer around attacks**: who is selected, when companions follow/retreat/rest, how servants inherit combat intent and how boss movement differs outside attack methods.

This should stay separate from `CHARACTER-COMBAT-CATALOG.md`. A projectile pattern is not the same thing as the Goal logic that decides when/why it is used.

## 1. Garnet combat-intent stack: guard / support / annihilate

Magical girls generally register three distinct targeting motives.

### Owner hurt by target — guard

`EntityGarnetAIOwnerHurtByTarget`:
- requires claimed/enabled tameable;
- reads owner's current AI revenge target;
- watches the owner's revenge timestamp;
- when a new revenge event appears, validates that attacker and assigns it as the companion's target.

This is the engineering basis for the player-facing **guard/protect owner** behavior.

### Owner hurt target — support

`EntityGarnetAIOwnerHurtTarget`:
- also requires claimed/enabled tameable;
- reads the owner's last-attacker/attack-history slot used by vanilla tameable-owner support AI;
- watches its timestamp;
- assigns that entity as the companion's target when the event changes.

This is the **join the owner's current fight** path.

### Nearest hostile — annihilate

Lower-priority nearest-target Goals search nearby categories such as:
- `EntityMob`;
- Slime;
- AmbientCreature for some characters;
- flying/high-priority hostile categories.

Therefore combat intent is layered:

`owner in danger → owner's combat target → autonomous local hostility`.

Technique:
**separate event-driven owner protection from autonomous target acquisition**.

Modern ANCHOR should preserve these as independently configurable intent sources instead of one opaque “attack nearest” Goal.

## 2. Friendly-fire / capability filtering in Garnet target base

`EntityGarnetAITarget.isGarnetSuitableTarget` centralizes policy.

It rejects:
- null/self/dead targets;
- Creeper unless attacker supports `canAttackExplosive()`;
- Ghast / `IGarnetEnemyFlying` unless attacker supports `canAttackFlying()`;
- enabled Garnet tameables owned by the same player;
- the tameable's own owner;
- out-of-home-range entities;
- unseen entities when sight checking is enabled;
- unreachable entities when `nearbyOnly` is enabled.

Technique:
**target capability gates belong in the shared suitability policy, not in every attack Goal**.

For ANCHOR, replace concrete-class categories with tags/traits where possible.

## 3. Flying-target acquisition is a multi-query special path

When `IGarnetEnemyFlying.garnetEnemySelector` is supplied, `EntityGarnetAINearestAttackableTarget` does not perform one ordinary query.

It separately scans a ±32 cube for:
- requested target class through selector;
- Ghast;
- Dragon;
- Wither;
- `EntityHomulillyNutcracker`.

Optionally, `allTarget=true` adds another normal target-class query.

All results are merged, sorted by distance and suitability-filtered.

This is the source of the already-recorded **Garnet→QB reverse dependency**: the generic Garnet AI imports the concrete Nutcracker class.

Performance note:
`continueExecuting()` returns:
`super.continueExecuting() && this.shouldExecute()`.

So maintaining an existing target can rerun the full acquisition path, including multi-AABB query + sort, rather than only validating the current target.

Technique worth preserving:
**high-priority tactical categories**.

Implementation to replace:
**re-acquisition scan inside continue validation**.

## 4. TNT avoidance is character-selective

`EntityMadomagiAIAvoidEntity` is registered against `EntityTNTPrimed` for:
- Madoka;
- Sayaka;
- Mami;
- Kyouko;
- Kirika;
- Yuri.

Homura does **not** register this TNT-avoid Goal, consistent with her own TNT-based combat identity.

Behavior:
- avoidance radius 16;
- selects an escape point up to 16 horizontal / 7 vertical away from the danger;
- requires the chosen point to increase distance from the threat;
- far speed usually 1.0;
- within distance-squared 81 (9 blocks), speed increases to 1.67.

Technique:
**character identity includes hazard-response policy**, not only weapons.

This is highly reusable for future AI personality:
- explosives specialist can ignore self-domain hazards;
- ordinary ranged units proactively flee them.

## 5. Wild QB avoids players until contracted

QB uses the same AvoidEntity Goal against `EntityPlayer`:
- 16-block radius;
- far speed 0.8;
- near speed 1.33.

But the Goal immediately refuses execution once QB is enabled/contracted.

Thus one ownership bit switches the NPC from:
**skittish wildlife → commandable follower/economy NPC**.

Technique:
**relationship state replaces an entire behavior layer**.

## 6. Follow-owner hysteresis and teleport fallback

`EntityGarnetAIFollowOwner` uses two distance thresholds.

Given constructor distance parameter D:

### Follow/normal mode
Start following beyond:
`D*2 + 3`.

Continue until within:
`D + 1`.

### Free mode
Start following only beyond:
`D*4 + 6`.

Once activated, continue until within:
`D*2`.

This creates broad hysteresis:
- Free lets NPC roam much farther before recall;
- once recalled, it still closes a substantial portion of the distance.

Every ~10 ticks it asks navigation to approach.

If pathing fails and distance squared >=225 (>=15 blocks):
- scans a 5×5 ring around owner;
- requires solid top surface and two free blocks;
- teleports the companion there.

Technique:
**pathfinding first, bounded safe-position teleport as recovery**.

## 7. Servant follow-master contract

`EntityGarnetAIFollowMaster`:
- starts when servant is >4 blocks from master (distance squared >=16);
- continues until within >2 blocks (distance squared >4);
- retries path every ~10 ticks;
- if path fails and distance >=12 blocks (squared >=144), uses the same 5×5 safe-ring teleport pattern.

This is a smaller/tighter version of owner following.

Together with servant lifetime rules, Garnet gives summons:
- combat-intent inheritance;
- spatial recovery;
- death → summon-readiness callback;
- master-death cleanup.

## 8. Standby is a hard tactical freeze with environmental escape

`EntityGarnetAIStandby`:
- active when unclaimed, or when Standby mode is selected;
- refuses to hold Standby if in water or not on ground;
- clears navigation on start.

The tameable entity separately switches Standby→Follow when stranded by water/air conditions.

Technique:
**stationary command mode must contain an anti-stranding escape rule**.

## 9. Mami “Tea Time” is an AI healing accelerator, not consumable use

`EntityMadomagiAITeaTime` executes only when:
- no attack target;
- entity is enabled;
- entity is injured;
- optional `whenChanged` form condition passes.

On start:
- sets held slot visually to a supplied ItemStack;
- Mami announces `Te Pomeriggio!`.

On reset:
- clears held slot.

On each AI update:
- calls `autoHealing()` `healPower` times.

No item is consumed by this Goal.

### Mami
Registration:
- Mami Tea visual item;
- `whenChanged=true`, which means exact ordinary transformed form is required;
- `healPower=3`.

Base living update already calls `autoHealing()` once server-side.
Mami therefore accumulates roughly four heal-timer increments per active tick.

With base transformed heal frequency 100, nominal idle Tea Time healing is roughly:
**1 HP per ~25 ticks (~1.25 s)**, assuming one base and one Goal update per server tick.

### Kyouko
Registration:
- red apple visual item;
- `whenChanged=false`;
- `healPower=1`.

That gives roughly two heal-timer increments/tick while resting:
**1 HP per ~50 ticks (~2.5 s)** at the common frequency100.

Technique:
**non-combat pose/prop doubles as a healing-rate modifier**.

This should not be confused with player drinking Mami Tea item effects.

## 10. Walpurgis non-combat wander is direct aerial roaming

`EntityMajoAIWalpurgisnachtWander` runs only without an attack target.

It chooses a destination:
- X/Z within roughly ±50 blocks;
- Y = local heightmap +10..20;
- rejects points within distance squared <225, so destination must be at least15 blocks away.

Movement:
- direct normalized velocity toward point at speed0.3;
- yaw faces velocity;
- new point on arrival or after long timeout.

Technique:
**boss idle movement is spatially large aerial roaming, not vanilla ground Wander**.

This preserves boss presence even before aggro.

## 11. Nutcracker pursuit contains the same anti-air routine as Walpurgis

`EntityHomulillyAIMoveForTarget`:
- maintains a flight target within a few blocks of the victim;
- resamples if invalid, randomly 1/30 updates or when near the point;
- directly sets host velocity toward that point at speed0.05;
- faces movement direction.

It also copies the same airborne-target punishment structure:
- ~100 ticks airborne → forced `motionY -=10`;
- landing → strength-3 explosion;
- another ~100 punishment ticks → strength-6 explosion.

And, like both Walpurgis attack AIs, the final fallback applies Poison V for300 ticks to **theHost**, not `theTarget`.

Distributed `EntityHomulillyAIMoveForTarget.class` SHA-256:
`5537224d0d68874698e08e95892208b58b075dcdfde51aae8b61d1b4fdab1608`.

Bytecode after the strength-6 explosion loads `theHost` and invokes the potion-effect method on it.

This turns the self-poison finding into a **three-implementation shared/copy pattern**:
- Walpurgis Play;
- Walpurgis Attack;
- Nutcracker MoveForTarget.

Historical author intent remains unavailable, but a copied target-variable defect is now a stronger hypothesis than an isolated typo.

## 12. Liese adds a priority anti-air target layer

Liese registers:
1. hurt-by target;
2. custom nearest-player Goal that accepts only `!player.onGround`;
3. general Garnet targets;
4. lower-priority general player target.

So Liese is not air-only overall. Instead, **airborne players get a higher-priority target acquisition lane**.

This aligns with its flying nuisance role and the broader boss anti-flight design.

Technique:
**same target class can be registered twice with different eligibility and priority**.

## 13. Wheel explicitly excludes its own encounter family

`EntityMajoAIWheelNearestAttackableTarget` scans living targets but skips:
- Oktavia;
- other Wheels.

It then falls back to shared Garnet suitability.

Technique:
**kinetic minion projectile has explicit parent/sibling exclusion before generic faction filtering**.

ANCHOR should prefer encounter/faction IDs instead of concrete classes.

## 14. Rosso Fantasma escalates path failure into instant relocation

`EntityRossoFantasmaAIAttack`:
- pathfinds toward target;
- accumulates path-finding penalty by10 on bad final paths;
- if navigator has no path:
  - target within distance squared25 → use Kyouko middle lunge;
  - farther away → directly `setPosition(target.posX, target.posY, target.posZ)`.

This is effectively a **hard teleport-to-target fallback** with no explicit presentation cue.

It explains why the fragile1-HP clones can keep pressure despite navigation failure.

ANCHOR improvement:
use bounded safe-position teleport + visible cue rather than raw overlap position.

## 15. Servant Oktavia uses position-step flight, not normal navigation

`EntityServantOktaviaAIAttack`:
- selects a random point around target;
- rejects it until the minimum of host→point and target→point squared distances is >=100 (at least10 blocks from both);
- every2 ticks, directly moves the servant **3 blocks toward that point** using `setPosition`;
- changes waypoint on proximity or timeout;
- melee checks every tick, with5-tick attack cooldown when close enough.

At nominal timing, the direct positional stepping can approach **30 blocks/s** of displacement during active updates.

This is closer to a scripted dash/orbit entity than a normal flying Mob.

Risks:
- direct `setPosition` bypasses ordinary navigation path choice;
- waypoint selection does not visibly test an air volume in this method;
- collision/clipping behavior needs runtime observation.

Technique:
**high-speed servant movement through deterministic positional stepping**.

## 16. Generic melee Goal has path-failure backoff

`EntityGarnetAIAttackOnCollide`:
- recomputes path after a short random delay;
- bad/missing final paths add +10 to `failedPathFindingPenalty`;
- that penalty is added to the next path-retry delay;
- Goal stops when penalty reaches100;
- attack cadence and attack-range padding are constructor parameters.

Technique:
**failed pathfinding increases future retry interval**, preventing a completely tight retry loop.

This is a useful old design concept even though modern Goal/navigation APIs differ.

## 17. Tactical AI primitives worth preserving

Keep independently:

1. owner-revenge guard trigger;
2. owner-offense support trigger;
3. autonomous annihilation target layer;
4. shared faction/capability suitability policy;
5. high-priority flying-target lane;
6. character-specific hazard avoidance;
7. relationship-state replacement of avoidance behavior;
8. owner-follow hysteresis;
9. pathfail safe teleport;
10. servant master-follow/lifetime contract;
11. hard Standby with anti-stranding escape;
12. non-combat prop-driven heal acceleration;
13. aerial boss roam independent of attack AI;
14. anti-air punishment controller;
15. priority anti-air player targeting;
16. sibling/parent exclusion for kinetic minions;
17. teleport fallback for disposable clones;
18. direct positional-step flight;
19. path-failure retry backoff.

The strongest architectural lesson is that **combat identity is distributed across targeting, hazard response, follow rules, rest behavior, movement and attack patterns**. Reconstructing only the attack method would lose much of the original character behavior.

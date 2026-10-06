# Five Difficulties X1 Preservation Port — P3 Sakuya time-domain exact static contract

Date: 2026-10-07

Canonical X1 archive:
- SHA-256 `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`

This document replaces the P1 approximate Sakuya timing/policy notes with direct source-backed findings from the reacquired canonical X1 archive.

## Primary source receipts

| Source | SHA-256 |
| --- | --- |
| `sources/java/thKaguyaMod/entity/item/EntitySakuyaWatch.java` | `738964897deeb1b2ee30767e032d13274f142825693f5e1995b89d88d3aaac01` |
| `sources/java/thKaguyaMod/entity/item/EntitySakuyaStopWatch.java` | `ac43880e034654931f4c7ccc9ee9e3170ce57792b8306a664ea22f8f55ebed49` |
| `sources/java/thKaguyaMod/item/ItemSakuyaWatch.java` | `6e4b88a6ec59134e4de46218edfbea77c05d2d46e0c3961e35e41e0ac121b185` |
| `sources/java/thKaguyaMod/item/ItemSakuyaStopWatch.java` | `d16ef5bd2be35eabc8cbe8321c37ba8085c6049bc3025c87467b88b9756ea5f8` |
| `sources/java/thKaguyaMod/event/THKaguyaTimeStopEventHandler.java` | `d89406801ec24187ad421dd147d64c24880432bf05f51d1c070de52dc528eb4f` |
| `sources/java/thKaguyaMod/entity/spellcard/THSC_SatuzinDoll.java` | `cbf570e6defe08bced6c4757d0083a022673f9ce2c4371d25afbcd2467c1d9c9` |

Selected distributed classes:
- `EntitySakuyaWatch.class` SHA-256 `be866de12c2c2977737c0f6d78b3cda3711b19f8693a89ca43c70c76d3fdcfdf`
- `EntitySakuyaStopWatch.class` SHA-256 `cd661d3c276464d5350e4ea5448aaed0953c3772464b7b698e2dc00da0d4e6f8`
- `ItemSakuyaWatch.class` SHA-256 `fdd07226c94618e0e9b90f52fb812dc2c635136379a2c322bfb7d7ad0cdd2271`
- `ItemSakuyaStopWatch.class` SHA-256 `6638ba4d482d83f41d4ecd33bf1564f518af1601dc91993c4ea9752e76ce109b`

## Mode constants

`EntitySakuyaWatch`:

- `TIME_STOP = 0`
- `TIME_STOP_IN_SPELLCARD = 1`
- `TIME_HALF = 2`
- `TIME_STOP_WITH_LIMIT = 5`
- `TIME_HALF_WITH_LIMIT = 6`

Source also contains internal branches for modes 3 and 4 that transition at tick 45 to full-stop / half-speed respectively. No constructor/call-site in the canonical source tree was found that creates those modes. Treat them as **dormant legacy branches**, not normal player-facing modes.

## Field geometry

The active watch entity follows the user through:

`THKaguyaLib.itemEffectFollowUser(watch,user,1.2D,-30F)`

The watch center is therefore approximately:
- 1.2 blocks from the user;
- at yaw offset -30° relative to user orientation;
- pitch-following;
- vertically near user eye height minus 0.5.

The effect query is:

`watch.boundingBox.expand(40,40,40)`

Therefore the X1 time field is **AABB/cube-like**, not a 40-block sphere.

P0/P1's sphere-style generic range model must not be treated as X1 exact for the Watch.

## Entities affected

X1 time manipulation iterates ordinary Minecraft **Entity** instances only.

No active source path freezes:
- block scheduled ticks;
- fluid scheduled ticks;
- BlockEntities;
- particles;
- animated textures;
- chunk/random ticks;
- world day time.

The old world-time rewind code is present only as commented code.

Therefore P3 must not import Roundabout's block/fluid/chunk/texture/particle freezing by default.

Entity categories therefore include, unless excluded:
- living mobs;
- other players;
- ItemEntity;
- TNT entity;
- falling-block entities;
- minecarts/boats;
- arrows/projectiles;
- THShot danmaku;
- XP orbs and other ordinary Entities.

## Exclusions

The watch does not apply time manipulation to:

1. the `userEntity` / source user;
2. an entity whose `riddenByEntity == userEntity` (the mount/vehicle the user is riding in the legacy relation model);
3. `EntityItemFrame`;
4. `EntityPainting`;
5. any entity with `ticksExisted < 2`.

Spell-card exception:
- if target is `EntitySpellCard`;
- `spellCard.canMoveInTimeStop == true`;
- `spellCard.user.equals(watch.userEntity)`;

then the card is not frozen and `specialProcessInTimeStop()` is invoked.

This is used by `THSC_SatuzinDoll`.

## New-entity grace

Both Watch and StopWatch only manipulate an entity when:

`hitEntity.ticksExisted >= 2`

This means a projectile/entity created during stopped time receives an approximately **two-tick grace window** before entering the normal freeze logic.

This is the correct X1 replacement for Roundabout's generic gradual-deceleration donor behavior.

P3 policy:
- X1 behavior = `NEW_ENTITY_GRACE_2_TICKS_THEN_FREEZE`;
- Roundabout `ROUNDABOUT_DECELERATE` remains engineering reference only.

## Full-stop algorithm in X1

Modes:
- TIME_STOP
- TIME_STOP_IN_SPELLCARD
- TIME_STOP_WITH_LIMIT
- StopWatch always uses full-stop behavior.

For each eligible Entity after it has already had an ordinary entity update:

- position is restored to `prevPosX/Y/Z`;
- yaw/pitch restored to previous values;
- motion X/Z forced to zero;
- airborne motion Y forced to zero;
- air set to zero;
- `ticksExisted--`;
- fallDistance reduced by `0.076865F`.

For LivingEntity:
- head yaw restored;
- `attackTime++`;
- Creeper state reset to -1;
- Ghast `attackCounter--`;
- tameables receive tiny `motionY -= 0.000001`;
- EntityPlayerMP receives explicit network teleport to previous position.

This is a **post-tick rewind/freeze hack**, not native tick cancellation.

### Modern P3 implementation rule

Roundabout-style tick cancellation is allowed as the 1.20.1 machinery because it better implements the intended observable contract without reproducing fragile 1.7.10 field hacks.

However the policy must remain X1:
- only Entity;
- source/exclusions above;
- two-tick new-entity grace;
- X1 field geometry;
- no block/fluid/particle/world freeze.

Any difference from the old post-tick corrections is an implementation modernization, not a changed player-facing rule.

## THShot resume behavior

`EntityTHShot` explicitly detects frozen time.

It stores:
- `lastTime`;
- `lastShotMotionX/Y/Z`.

When its age does not advance:

`ticksExisted <= lastTime`

the shot exits its update early.

When time advances again, it restores:

`motionX/Y/Z = lastShotMotionX/Y/Z`

before resuming shot logic.

Therefore X1 danmaku naturally resumes its pre-freeze motion after the Watch stops manipulating `ticksExisted`.

This confirms that a modern tick-cancellation implementation should **preserve projectile velocity/state**, not zero it permanently.

## Half-speed algorithm

Modes:
- TIME_HALF
- TIME_HALF_WITH_LIMIT.

The Watch calls:

`slowDownSpeed(entity,1,2)`

Every Watch update:
- `timeRate = 1/2`;
- subtracts half of the just-observed `pos - prevPos` from entity motion;
- adjusts fallDistance by half of the legacy compensation value.

On Watch `count % 2 < 1` (every other Watch count):
- `ticksExisted--`;
- Living head yaw is restored;
- Creeper state reset;
- Ghast attackCounter decremented.

The old implementation is therefore not a clean half-rate scheduler; it is a post-update motion/timer correction.

P3 modern policy may use **alternate-tick entity cancellation** for the intended half-speed effect, but must record this as a modernization and keep the X1 phase deterministic.

## Duration / lifecycle exactness

### Spell-card Watch

Source condition:

`mode == TIME_STOP_IN_SPELLCARD && ticksExisted > 60`

The entity calls `setDead()` at Watch tick 61, but the method does not return immediately and can continue the same update.

Static representation:
- nominal threshold: 60;
- final update can execute at tick 61;
- modern exact-policy constant: **61 field-processing updates maximum** unless runtime measurement proves a different removal timing.

### Limited full stop

Source:

`TIME_STOP_WITH_LIMIT && ticksExisted > 100`

Same no-immediate-return structure after `itemEffectFinish`.

Modern static contract:
- threshold 100;
- final processing update can occur at tick 101;
- represent as **101 maximum field-processing updates**.

### Limited half speed

Source:

`TIME_HALF_WITH_LIMIT && ticksExisted > 160`

Modern static contract:
- threshold 160;
- final processing update can occur at tick 161;
- represent as **161 maximum field-processing updates**.

### StopWatch

Source:

`if(ticksExisted > 40) { setDead(); return; }`

This one returns immediately.

Modern static contract:
- **40 processing updates**.

### Persistent creative modes

TIME_STOP / TIME_HALF have no fixed auto-expiry.

The Watch ends when:
- after tick 10, user sneaks;
- user is hurt;
- user disappears/dies;
- no player remains in field;
- duplicate Watch conflict occurs.

Creative mode has continuous exhaustion disabled.

## Item activation

`ItemSakuyaWatch`:

Item damage / metadata selects mode:
- 0 = half-speed branch;
- 1 = full-stop branch.

Sneak-right-click can toggle 0 ↔ 1, guarded by player `ticksExisted % 2 == 0`.

Max charge:
- damage 0: 20 ticks;
- damage 1: 48 ticks.

Creative:
- right-click immediately invokes activation;
- mode 0 → persistent TIME_HALF;
- mode 1 → persistent TIME_STOP.

Survival:
- requires food >0;
- must complete full charge;
- damage 0 → TIME_HALF_WITH_LIMIT;
- damage 1 → TIME_STOP_WITH_LIMIT;
- item stack is consumed when field starts;
- normal Watch modes later return the Watch item through `itemEffectFinish`.

Duplicate-precheck before spawn searches only a 20-block AABB for existing `EntitySakuyaWatch`.

## StopWatch activation

`ItemSakuyaStopWatch`:
- immediate right-click;
- duplicate-precheck within 20 blocks rejects if Watch **or** StopWatch exists;
- spawns `EntitySakuyaStopWatch`;
- non-creative consumes item;
- StopWatch does not return itself after use;
- full-stop field behavior;
- terminates on user damage;
- 40 field-processing updates.

## Double-controller behavior

Watch:
- encountering another `EntitySakuyaWatch` in its 40-block field causes item-return/termination behavior for both.

StopWatch:
- encountering Watch or StopWatch in its 40-block field kills/conflicts the controllers.

This should become one modern **single-active-time-controller conflict rule**, scoped close to the X1 behavior.

## Player count

Both controller entities count EntityPlayer inside the 40-block field.

If count becomes zero:
- Watch returns/finishes;
- StopWatch dies.

Because the controller follows a player source, ordinary player usage normally keeps at least the source player in range.

## Spell-card exception: Murdering Doll

`THSC_SatuzinDoll`:
- at spell time 36, creates a Sakuya Watch in TIME_STOP_IN_SPELLCARD mode if the same user's Watch is not already nearby;
- its spell implementation returns `canMoveInTimeStop() = true`;
- Watch therefore lets the spell-card entity continue and explicitly calls `specialProcessInTimeStop()`;
- base `THSpellCard.specialProcessInTimeStop` extends endTime by one each call;
- Murdering Doll uses that callback to transform selected frozen red/blue knives into green knives during time stop.

This is an intentional **same-owner executable-during-stop exception**, not a generic projectile exemption.

## Event handler status

`THKaguyaTimeStopEventHandler` contains an EntityEvent subscriber but no active freeze implementation.

It does not contribute time-stop behavior in this snapshot.

The effect lives in the controller entities themselves.

## P3 modernization boundary

Roundabout contributes:
- safe 1.20.1 tick interception;
- server/client synchronization patterns;
- interpolation-freeze patterns where needed.

X1 defines:
- controller center;
- 40-block AABB field;
- entity-only scope;
- exclusions;
- new-entity 2-tick grace;
- full-stop / half-speed policies;
- duration/lifecycle;
- spell-card exception.

Do not import Roundabout defaults that X1 did not have.

# QB-MOD 1.6.4.082 — Witch / boss combat catalog

Primary evidence: supplied QB-MOD source snapshot.

Community material is used only as reconnaissance. Contemporary gameplay descriptions report that Homulilly can be handled from range and that prolonged boss fighting can heavily damage large player-built structures; these are consistent with the source's teleport/TNT and world-destruction mechanics, but source remains authoritative.

## Kriemhild Gretchen

Source:
- `EntityKriemhildGretchen.java`
- `EntityKriemhildAIAbsorb.java`

Attributes:
- 2000 HP;
- size 10 × 30;
- follow range 64;
- nominal movementSpeed 3.75;
- 3 attack damage.

### Absorb pulse

Every 40 ticks the AI runs a pulse:
- scans living entities in ±64 X/Z and ±32 Y;
- processes at most ~101 targets;
- normally attacks eligible non-Creepers and heals Kriemhild by 2 for each successful hit;
- when the internal timer reaches 160, the pulse instead creates lightning effects at selected targets;
- timer resets after that 160-tick cycle.

Technique: **periodic large-area drain/heal pulse with a slower presentation/escalation beat**.

### Damage gate

Damage handling contains:
- fire immunity;
- super-armor behavior;
- reduced acceptance of source-less/environment damage;
- self-damage rejection.

On low/death state server-side it creates an enormous explosion with strength 80 and drops a Grief Seed.

Risk:
- large AABB scan and up-to-100 target processing every 40 ticks;
- explosion strength 80 is destructive and expensive;
- ANCHOR should budget both entity scan and block consequences.

---

## Homulilly

Source:
- `EntityHomulilly.java`
- `EntityHomulillyAIAttack.java`

Attributes:
- 40 HP;
- size 3 × 5;
- movementSpeed 0.2;
- attack 8;
- follow range 24.

### Hit reaction / teleport defense

When damaged server-side:
- self-originated damage heals 1 and is rejected;
- on roughly 1/3 of incoming attacks, attempts up to 64 random teleports;
- after a successful evade, if attacker is living, places/throws TNT pressure back at that attacker and rejects the original damage.

Technique: **probabilistic damage-avoidance teleport coupled to retaliation**.

### Combat loop

Attack AI:
- periodically attempts a 3-point TNT pattern around target;
- next attack delay random 50–99 ticks after success;
- separately teleports at random intervals;
- if line-of-sight is lost, repeatedly attempts `teleportToEntity`.

`teleportToEntity` chooses a destination approximately 16 blocks on the far side of the target vector plus random offsets.

Technique: **line-of-sight recovery by target-relative teleport**, not by pathfinding alone.

---

## Homulilly Nutcracker

Source: `EntityHomulillyNutcracker.java`

Attributes:
- 60 HP;
- size 8 × 16;
- attack 8;
- follow range 64.

### Damage throttle

- incoming damage >=1 is reduced to 1;
- source-less damage is often rejected;
- 20-tick super-armor blocks follow-up hits;
- attacks from Homulilly servants heal the boss by 1 and are ignored;
- legacy code also forcibly disables creative/flying player capability flags.

Technique worth preserving: **1-damage gate + fixed super-armor window**.
Legacy capability mutation must not be ported.

### Destructive movement

Every living update:
- checks collision boxes expanded around the huge body;
- destroys encountered non-bedrock blocks;
- drops them with 30% chance;
- fighting state slightly expands vertical destruction zone.

Melee also applies very high forward knockback.

Technique: **giant body collision as a terrain deformation volume**.

ANCHOR rewrite should use the LAB bounded block-edit system and encounter protection rules.

---

## Oktavia

Source:
- `EntityOktavia.java`
- `EntityMajoAIOktavia.java`
- `EntityWheel.java`

The boss delegates most ranged pressure to Wheels.

### Wheel pattern

When target is not in melee range:
- tries up to 20 random spawn positions in a roughly 10-block local cube;
- requires Wheel `getCanSpawnHere()`;
- launches the Wheel toward target by directly setting motion;
- emits up to 5 Wheels with 5-tick spacing;
- after the fifth, pauses 60 ticks.

If target is close:
- direct melee, 20-tick cooldown.

Technique: **five-shot kinetic-minion burst with randomized launch origins**.

Static anomaly:
- `spawnWheel` contains `System.out.println(false)` on every candidate attempt and `System.out.println(true)` on success.
- In active combat this can spam stdout heavily and is a clear cleanup/performance candidate.

---

## Charlotte

Source:
- `EntityCharlotte.java`
- `EntityMajoAICharlotte.java`

Charlotte has explicit first/second form state.

### Form replacement

If revivable state is active and current entity is first form:
- spawns a new Charlotte at same location;
- new entity is marked second form;
- revenge target is copied;
- old entity is killed via superclass path.

`setDead()` can also spawn a second-form replacement with a remaining revival count. An initial sentinel value can randomize the total remaining revivals.

Technique: **entity replacement as phase transition**, carrying combat aggro/state forward.

### Second-form terrain interaction

Second form:
- checks collisions around its body;
- destroys blocks except bedrock, Mami Ribbon and Kyouko Shield;
- dropped items use 30% chance;
- slows its own motion when breaking blocks.

Technique: **phase-specific collision destruction**.

---

## Ophelia

Source: `EntityOphelia.java`

Ophelia supports phantom copies.

- non-phantom master can spawn phantom Ophelia after age/target conditions;
- phantom HP is clamped to 1;
- phantom dies if master dies;
- master tracks phantom count and limits spawning;
- phantom death decrements the master's count.

Technique: **master-owned decoy/phantom pool with count accounting and parent lifetime dependency**.

---

## Candeloro

Source: `EntityCandeloro.java`

Simpler melee boss:
- 40 HP;
- 8 attack;
- applies very strong Slowness (amplifier 4) on hit;
- creates Maid Puella Magi servants.

Technique: **melee crowd control + servant ecosystem**.

---

## Gertrud

Source: `EntityGertrud.java`

- 40 HP, 10 attack;
- conventional melee;
- servant factory randomly chooses Adelbert or Anthony.

Technique: **simple boss with heterogeneous servant pool**.

---

## Walpurgisnacht relationship to this catalog

Walpurgisnacht remains documented in depth in `ANALYSIS-INITIAL-2026-10-07.md`.

Its recovered technique set includes:
- timed world encounter gate;
- global ambience mutation;
- phase threshold;
- 1-damage + super-armor gate;
- offset-point airborne repositioning;
- multi-timer Flame Lance / Prickle pressure;
- anti-air punishment;
- terrain-to-TNT conversion;
- Prickle → Shadow Puella Magi delayed summon;
- encounter death staging and cleanup.

It should be treated as an **encounter controller + boss combatant**, not merely another hostile mob.

---

## Failure / anomaly leads added by this pass

These are source-level candidates only, not historically proven bugs:

1. Oktavia AI stdout spam in `spawnWheel`.
2. Homulilly AI's `getRNG().nextInt(1)` is always 0, so its apparent attack-type selection has only one reachable branch.
3. Homulilly/other teleport loops may attempt up to 64 destinations in one AI update.
4. Charlotte/Nutcracker collision destruction performs synchronous block removal in living updates.
5. Kriemhild can scan a very large volume and affect up to ~101 living targets per 40-tick pulse.
6. Huge Kriemhild terminal explosion may be an extreme TPS/world-damage event.
7. Legacy creative/flying capability mutation repeats outside Walpurgisnacht in Nutcracker.

These should be matched against historical reports if older forum/archive material is later recovered.

## Reusable boss-technique categories

- periodic AOE drain/heal;
- low-frequency telegraphed escalation pulse;
- probabilistic teleport evade + retaliation;
- line-of-sight recovery teleport;
- damage cap + super-armor;
- collision-volume terrain destruction;
- kinetic-minion projectile burst;
- phase transition through entity replacement;
- parent-owned phantom pool;
- servant-pool boss;
- projectile-to-delayed-minion seed;
- encounter-scoped environment controller.

Preserve them independently.

## Nutcracker anti-air movement detail

A later tactical-AI pass found that `EntityHomulillyNutcracker`'s `EntityHomulillyAIMoveForTarget` is more than a movement Goal.

It:
- pursues small randomized flight points around its current target;
- after ~100 airborne target ticks, enables the same forced-down anti-air punishment used by Walpurgis;
- subtracts10 from target vertical motion every punishment update;
- creates strength-3 explosion on landing;
- after another100 punishment ticks without grounding, creates strength-6 explosion.

The final fallback then applies Poison V for300 ticks to **the Nutcracker host**, not the target. Distributed bytecode confirms the host object receives the potion effect.

This makes anti-flight control a **shared boss-family technique**, and the self-poison target choice a repeated implementation anomaly rather than a one-off Walpurgis oddity.


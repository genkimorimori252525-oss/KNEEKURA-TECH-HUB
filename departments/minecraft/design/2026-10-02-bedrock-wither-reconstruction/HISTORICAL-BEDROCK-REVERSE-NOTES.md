# Historical Bedrock Reverse-Engineering Notes — Wither

Reviewed: 2026-10-02  
Status: HISTORICAL / HYPOTHESIS SUPPORT ONLY

Source:
`PeratX/source` at `ea30a251dd8fd16a7bd2e568209797a9c7be970f`

The repository labels itself "Minecraft: Bedrock Source" and contains generated/decompiled C-like output. Its exact Bedrock game version is not established here. Therefore **no numeric constant from this source is current-authoritative**.

Current BDS structure remains authoritative over this file:
[BDS-STRUCTURE-2026-10-02.md](BDS-STRUCTURE-2026-10-02.md)

## Highest-damage target — strong historical corroboration

Historical `WitherTargetHighestDamage::getHighestDamageTarget()`:

- reads a Wither-owned "player party" collection;
- resolves each entry back to a Player;
- compares the stored damage value;
- chooses the Player with the greatest value that passes target validation;
- `canContinueToUse` stops when the highest-damage Player changes.

This matches the current BDS structural signature:

```
Player* getHighestDamageTarget()
```

Engineering consequence:
KNEEKURA's priority-1 highest-damage Goal currently selects Players, while the broader threat ledger can still retain non-player attackers for diagnostics and lower-priority retaliation logic.

Do not infer current damage-window duration, reset rules or party-entry lifetime from this historical build.

## Random attack-position goal — relationship evidence

Historical `WitherRandomAttackPosGoal`:

- is derived from `RandomStrollGoal`;
- only considers use when the Wither has a target;
- refuses the path while the Wither is in its powered/second-state condition;
- consults a Wither-owned wants-to-move flag;
- marks Wither pathing on start;
- clears wants-to-move/pathing on stop;
- modifies flight speed while active;
- assigns a shot delay when the movement goal stops.

Current BDS independently still exposes:
- `WitherRandomAttackPosGoal : RandomStrollGoal`;
- goal-local `mIsPathing`;
- Wither fields `mWantsMove`, `mIsPathing`, `mFramesTillMove`, `mMovementTime`;
- shot timing fields `mDelayShot`, `mTimeTillNextShot`, `mTimeSinceLastShot`.

This makes the **movement ↔ pathing ↔ firing-delay relationship** a high-priority current-runtime measurement target.

Rejected as current constants:
- historical flight-speed multiplier;
- historical stop-shot delay;
- historical random-position range values.

## Difficulty-health historical behavior

Historical `reloadHardcoded` visibly modifies health limits by difficulty and separately records a half-health threshold.

This supports the idea that the public JSON base health=600 is subsequently difficulty-adjusted in native code. It does **not** replace current runtime measurement for exact values, even though maintained current gameplay documentation reports 300/450/600.

## Phase transition historical relationship

Historical damage handling:
- processes accepted damage;
- tracks health interval values;
- compares health against a stored threshold;
- calls `changePhase` when threshold/phase conditions are met.

Current BDS still exposes:
- `mHealthThreshold`;
- `mPhase`;
- `mHealthIntervals`;
- `mLastHealthValue`;
- `mWantsToExplode`.

This is strong structural continuity but not proof of unchanged phase math.

## Projectile creation

Historical `_performRangedAttack(head, targetPos, dangerous)` selects between two projectile definitions based on the dangerous flag. Current Mojang behavior packs independently expose separate normal and dangerous skull entity definitions.

Accepted invariant:
normal/dangerous projectile identity is an explicit boss decision.

Not accepted from historical source:
- old head offsets;
- old exact firing cadence;
- old entity numeric IDs.

## Block destruction

Historical code had a `canDestroy` predicate excluding Bedrock, portal/portal-frame, command-block family and several education/barrier-like blocks.

Current BDS has evolved the interface into:

```
canDestroy(Block const&, WitherAttackType)
_destroyBlocks(..., range, WitherAttackType)
```

with distinct:
- Charge
- HurtExplosion
- Projectile

Therefore old one-size block exclusions are **not** sufficient for current reconstruction. They are only a candidate baseline for per-attack-type runtime tests.

## Rules for use

Historical Bedrock reverse engineering may:
- explain a current field/function name;
- identify a relationship worth measuring;
- provide search terms for current symbols;
- suggest test scenarios.

It may not:
- set a current timer/speed/range;
- override current Mojang JSON;
- override current BDS generated headers;
- bypass direct Bedrock measurement where behavior remains hidden.

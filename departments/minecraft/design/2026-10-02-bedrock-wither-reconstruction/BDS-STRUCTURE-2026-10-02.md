# Bedrock Wither — Current BDS Structural Map

Reviewed: 2026-10-02  
Purpose: map current Bedrock Dedicated Server Wither structure before assigning Java behavior.

## Current BDS anchor

Source surface: LiteLDev/LeviLamina generated Bedrock headers.

Current main checked:
`1bab1522cdfd697d241e77fe60f19b9db2a20a5a`

Immediately previous inspected parent:
`32fcaa02baa38371b705358801c7d185c284233e`

The following relevant files have identical blob SHAs across both commits:

| File | blob SHA |
|---|---|
| `WitherBoss.h` | `03cd288d06c8c053678a51891c014d0d910e94e5` |
| `WitherTargetHighestDamage.h` | `1857b2a20df2b86f07e4d661a09e67ad709a5057` |
| `WitherRandomAttackPosGoal.h` | `258cdeb206ac193336e8d90ba598a6695bd42ad1` |
| `WitherBossPreAIStepResult.h` | `6d02f203c934b22240e1cf63598e3de8cce78524` |
| `tooth.json` | `68a8054ee0cf71390c80b3d21c66921ed0c9f272` |

The current LeviLamina package declares:
- loader line: 26.51.x
- BDS dependency: `github.com/LiteLDev/bds = 1.26.51`
- supported server version: 26.51.1

This file treats the generated headers as **current Bedrock structure evidence**, not source-body evidence.

## WitherBoss attack categories

Current BDS declares:

```
WitherAttackType
0 Charge
1 HurtExplosion
2 Projectile
```

The same class exposes:
- `_destroyBlocks(Level&, AABB const&, BlockSource&, int range, WitherAttackType)`
- `canDestroy(Block const&, WitherAttackType)`

Implication:
Bedrock does not model all block destruction as one generic Wither action. Charge, hurt reaction and projectile destruction are distinguishable at the native API boundary.

KNEEKURA adaptation:
`BedrockWitherAttackType` mirrors only the names/IDs. Exact block predicates and ranges remain unimplemented until stronger evidence exists.

## Current WitherBoss runtime fields

The generated class exposes these member fields:

### Shield / phase
- `MAX_SHIELD_HEALTH`
- `mShieldHealth`
- `mHealthThreshold`
- `mPhase`
- `mWantsToExplode`

### Heads
- `mHeadRots[3]`
- `mOldHeadRots[3]`
- `mNextHeadUpdate[3]`
- `mIdleHeadUpdates[3]`
- `mlastFiredHead`

### Charge
- `mCharging`
- `mChargeDirection`
- `mChargeFrames`
- `mPreparingCharge`

### Projectile cadence
- `mProjectileCounter`
- `mTimeTillNextShot`
- `mFireRate`
- `mDelayShot`
- `mTimeSinceLastShot`
- `mSecondVolley`
- `mMainHeadAttackCountdown`
- `mAttackRange`

### Movement
- `mFramesTillMove`
- `mWantsMove`
- `mIsPathing`
- `mMovementTime`

### Skeleton / health tracking
- `mMaxHealth`
- `mNumSkeletons`
- `mMaxSkeletons`
- `mHealthIntervals`
- `mLastHealthValue`

### Other combat lifecycle
- `mDestroyBlocksTick`
- `mSpawningFrames`
- `mSpinSpeed`
- `mStunTimer`
- `mDeathSource`

These names strongly constrain what the Java reconstruction should be capable of representing, but do not reveal each field's initialization value or exact transition equations.

KNEEKURA now mirrors the non-pointer/runtime-observable subset in `BedrockWitherRuntimeState`. Unknown values default neutrally and are not claimed to be Bedrock defaults.

## AI step structure

Current BDS exposes:
- `preAiStep()`
- `postAiStep()`
- `aiStep()`
- `newServerAiStep()`

`WitherBossPreAIStepResult` contains:

```
0 StopAiStepExecution
1 RunAiStep
2 RunPostAiStepAndAiStep
```

Implication:
native Wither processing has an explicit pre-AI gate capable of suppressing or altering the normal AI-step sequence. The Java reconstruction should therefore not assume all states can be represented only through Goal priorities.

KNEEKURA action:
keep the high-level Java phase state machine separate from Goal selectors so spawn/transition/stun/charge states can later gate ordinary AI execution.

## Highest-damage goal

Current class:
`WitherTargetHighestDamage : TargetGoal`

Exposed members:
- reference to `WitherBoss`
- current `Mob* mTarget`
- `canUse`
- `canContinueToUse`
- `start`
- `_canAttack`
- `getHighestDamageTarget()`

Notably, current generated signature is:

```
Player* getHighestDamageTarget()
```

This is stronger structural evidence than the generic wording of public documentation.

KNEEKURA action:
- threat ledger may retain all attackers for diagnostics;
- priority-1 highest-damage Goal currently evaluates Players only;
- `hurt_by_target` and nearest-target paths remain responsible for non-player retaliation/acquisition;
- direct Bedrock runtime testing must confirm that this interpretation matches actual combat.

## Random attack-position goal

Current class:
`WitherRandomAttackPosGoal : RandomStrollGoal`

It adds:
- `bool mIsPathing`
- `start`
- `stop`
- `canUse`
- `canContinueToUse`

This is useful evidence that the native Wither special movement goal is structurally related to random-stroll behavior and tracks pathing explicitly.

Unknown:
- exact candidate-position generator;
- vertical distribution;
- target-relative offsets;
- path retry timing;
- interaction with `mFramesTillMove / mWantsMove / mMovementTime`.

Do not copy Java `RandomStrollGoal` movement blindly until these are measured or otherwise recovered.

## Java reconstruction rule

For each BDS field/function:

1. mirror the state/interface if it materially affects later observation;
2. do not invent its numeric default;
3. bind it to official JSON where public values exist;
4. otherwise seek direct Bedrock observation;
5. use historical Bedrock reverse engineering only as a version-labelled hypothesis;
6. use BEStyleWither only after all Bedrock-origin evidence is exhausted.

## Immediate high-value unknowns

- `mPhase` values and transition conditions
- `mHealthThreshold` initialization
- shield semantics and `MAX_SHIELD_HEALTH`
- `mProjectileCounter` / `mSecondVolley` sequence
- `mFireRate` and health-interval relationship
- `mPreparingCharge` / `mChargeFrames`
- skeleton counters and difficulty initialization
- per-attack-type block destruction predicates/ranges
- preAiStep result by spawn/phase/stun/death state

These are now preferred measurement/reverse-analysis targets.


## Random-stroll inherited fields versus exposed schema

Current C++ structural definition:
`WitherRandomAttackPosGoalDefinition : RandomStrollGoalDefinition`.

The parent definition contains:
- `mSpeedModifier`
- `mXZDist`
- `mYDist`
- `mInterval`

The ordinary Mojang `minecraft:behavior.random_stroll` schema exposes defaults:
- speed multiplier 1
- xz distance 10
- y distance 7
- interval 120

However, the current dedicated `minecraft:behavior.wither_random_attack_pos_goal` schema exposes only:
- priority
- control_flags

Therefore KNEEKURA does **not** assume the ordinary random-stroll numeric defaults are the effective native Wither values. The C++ inheritance proves field shape, not current initialized values. Those four values remain measurement/symbol-body targets.

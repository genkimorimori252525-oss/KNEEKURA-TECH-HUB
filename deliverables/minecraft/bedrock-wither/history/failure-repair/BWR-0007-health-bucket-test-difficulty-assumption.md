# BWR-0007 — health-bucket GameTest assumed Hard-scale health

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: REPAIR_IN_PROGRESS

## Symptom

Forge GameTest run `36993277835` failed:

`lasthealthintervaltrackslowesthealthin75pointbuckets failed! lastHealthInterval did not track the strict-lower 75-point bucket`

## Root cause

Basis: DIRECT_OBSERVATION + fixture inspection.

The test set Wither health to absolute values 499 and 401 while the GameTest server's active difficulty could produce a maximum health below those values (for example Easy max = 300).

Minecraft clamps `setHealth(...)` to max health, but the expected interval was still calculated from the unclamped literal. The product tracker and assertion were therefore evaluating different health values.

This was a test fixture assumption, not evidence that the 75-point Bedrock NBT rule was wrong.

## Repair

Derive test health values from the actual entity max health:
- first low point = `maxHealth - 1`;
- expected interval uses the same effective low point;
- heal to max and verify the interval does not increase;
- damage below the prior interval and verify monotonic decrease.

All Boss GameTests are also separated into unique batches to prevent cross-test combat effects.

## Verification

Pending dedicated Forge GameTest.

## Lesson

Difficulty-dependent bosses must never use hard-coded health fixtures unless the test explicitly pins difficulty. Assertions should derive values from the same runtime health domain they mutate.

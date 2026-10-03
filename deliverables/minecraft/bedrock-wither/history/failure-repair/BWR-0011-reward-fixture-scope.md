# BWR-0011 — reward fixture rejected unrelated terrain drops

Date: 2026-10-03
Origin: OWN_DEVELOPMENT / TEST_FIXTURE
State: VERIFIED_FIXED (two consecutive reused-world runs)

## Symptom

The new player-reward regression passed on its initial fixture, then a repeated run failed its precondition before damaging the boss. The diagnostic run reported `doMobLoot=true, existingOrbs=0, existingItems=5`; the other 23 GameTests passed. This was not a product reward failure.

## Root cause

Basis: DIRECT_OBSERVATION + generated-world NBT + source/mapped-bytecode inspection.

The reward observer counts XP and Nether Stars, but the precondition rejected every ItemEntity. Saved NBT identified the five matching entities as ordinary dirt, cobbled-deepslate and cobblestone drops, with no XP or Nether Star in the observation area. The structure origin was at y=-60, so moving the fixture up 64 blocks placed the boss at y=5, not necessarily above terrain. Its final explosion can produce those unrelated block drops.

An earlier draft also lacked complete cleanup. Review found that a failed drops-event assertion could leave already-spawned XP before the first normal reward sample. Those cleanup boundaries were repaired in the fixture as well.

## Repair

- Check only preexisting XP and Nether Stars, exactly matching the observed reward classes
- Keep exact 50-XP/one-star assertions and once-only normal Forge reward-hook assertions unchanged
- Discard the test boss before precondition failure
- Always unregister identity-scoped observers, collect outstanding test rewards and clean up only recorded reward UUIDs and the owned boss
- Keep the observations synchronous and describe them as per-call increases, not an exhaustive mutation ledger

Only the generated draft world was archived. The finalized suite then ran twice against the same world without a reset between those two runs. Both builds succeeded and **24/24 required GameTests passed**.

[Compact acceptance/fixture evidence](../../evidence/gametest-rewards-2026-10-03.json)

## Product conclusion and limits

Production behavior was unchanged. The test strengthens existing player attribution, death/loot/XP event and reward-idempotency acceptance; it does not establish a newly repaired product defect or a new Bedrock reward timing rule.

Ordinary XP may be destroyed by the final blast. The fixture therefore counts actual initial XP and observed positive changes plus normal Forge XP hooks, rather than requiring all orbs to survive. It cannot detect an unhooked award created and destroyed entirely within one synchronous call. Real ServerPlayer advancement grants, normal-world credit expiry and direct Bedrock timing remain unverified.

## Lesson

A fixture's preconditions must concern the actual assertion inputs. Unrelated terrain drops are not evidence of duplicated boss rewards, and repeated-run/failure-path cleanup must be verified separately from product behavior.

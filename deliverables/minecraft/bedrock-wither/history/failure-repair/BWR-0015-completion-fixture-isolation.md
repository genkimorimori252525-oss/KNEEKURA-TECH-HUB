# BWR-0015 — completion fixtures depended on incidental world state

Date: 2026-10-03
Origin: OWN_DEVELOPMENT / TEST_FIXTURE
State: VERIFIED_FIXED (local GameTests / independent review)

## Observed failures

- A relative +64 or +128 height did not guarantee open air: the GameTest origin was near worldY=-60 and reused fixtures/terrain affected movement and ground-contact assumptions
- An invulnerable, unregistered cow was correctly rejected by ordinary target-goal processing, so a reload test lost its target
- Bare `Entity.tick()` did not advance the engine-owned `tickCount`, preventing a side-head timing test from exercising its actual scheduler
- The built-in mock-server-player helper reached a null network channel during simulated login; this was fixture setup failure, not product RED
- A difficulty-changing test did not restore the previous difficulty after an assertion failure; on Hard, an old impact fixture's10-HP cow saturated a12-damage assertion
- Global nearby-projectile queries included another fixture's skulls; a reward precondition encountered ten old XP orbs in its shared low-altitude area

## Repairs

Use deliberately high absolute fixture positions, deterministic movement seeds, real registered eligible high-health targets, the ordinary `ServerLevel.tickNonPassenger` pipeline, scoped no-network Forge FakePlayers, and `finally` cleanup/restoration. Scope projectile assertions to their owning Wither. Give the old direct-impact target enough HP for every difficulty while retaining exact damage/effect assertions.

The reward observer keeps its empty-XP/empty-star precondition and exact50-XP/one-star checks. Its isolated area is now at max build height minus32, rather than deleting unrelated rewards or weakening the guard. New tests clean only their own entities/drops and restore placed blocks/listeners.

The final suite is repeated against the same generated world to test cleanup and repeatability. No user world or user computer is involved. These failures are not presented as Bedrock gameplay defects.

[Final completion evidence](../../evidence/source-completion-2026-10-03.json)

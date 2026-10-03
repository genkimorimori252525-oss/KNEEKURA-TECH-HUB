# BWR-0014 — source-defined death state and star lifetime were incomplete

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (local GameTests / independent review)

## Symptom and root cause

A first-phase killing hit left native Phase=1, retained combat momentum, and initialized a shield-flicker field that never progressed. Actual Nether Star loot used ordinary Java timed despawning despite the retained Bedrock drop description specifying no timed despawn.

Basis: documented NBT semantics, historical native death-body arithmetic, actual item ticks/NBT and four initial failing lifecycle/block-rule tests plus a separate star-lifetime RED.

## Repair

- Accepted death and older death saves normalize native Phase=0
- Accepted death cancels navigation and residual combat velocity
- An explicitly historical decreasing flicker divisor, initially15, toggles AirAttack-backed armor visibility and survives save/load
- Actual Nether Star loot receives Java's persistent unlimited-lifetime flag through the existing item-spawn path
- Charge rejects obsidian independently from dangerous-projectile block eligibility

The existing Forge cancellation, initial player attribution, death/loot/XP events, 50-XP/one-star count and reward-idempotency tests remain. Rewards are not moved to a historical delayed-death schedule. The star test runs through ordinary item expiry duration, saves/restores item NBT and runs through it again.

[Final completion evidence](../../evidence/source-completion-2026-10-03.json)

## Lesson

Keep diagnostic native phase, shield presentation and semantic death separate. Verify the actual dropped item lifecycle, not merely the loot-table item count.

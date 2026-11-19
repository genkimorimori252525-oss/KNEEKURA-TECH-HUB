# KNEEKURA Boss Combat Toolkit v1

Status: **REUSABLE DESIGN CONTRACT / NO SHARED RUNTIME LIBRARY REQUIRED**  
Anchor: Minecraft 1.20.1 + Forge  
Scope: boss and elite-mob combat engineering

This toolkit turns recovered boss-engineering knowledge into reusable contracts.
It is deliberately **not** a single mandatory boss framework.

A product may adopt one module, several modules, or none. The point is to give
implementation AIs a stable vocabulary, boundaries and acceptance tests without
forcing every boss into the same architecture.

## Core rule

```text
Behavior requirement
      ↓
choose only needed toolkit modules
      ↓
product-owned implementation
      ↓
read-only debug snapshot
      ↓
unit/GameTest/LAB verification
      ↓
adoption record
```

The toolkit defines **responsibilities and invariants**, not gameplay constants.

## Modules

| ID | Module | Owns | Does not own |
|---|---|---|---|
| BCT-A | Attack Lifecycle | attack arbitration, telegraph/commit/active/recovery/cooldown | boss-specific timing/damage |
| BCT-B | Beam Contract | authoritative beam geometry/hits + compact visual state | renderer art/style |
| BCT-D | Projectile Deflection | ownership/allegiance transition, post-deflection policy | arbitrary projectile physics |
| BCT-F | Temporary Faction | temporary controller/team/AI overlay on existing mobs | permanent entity conversion |
| BCT-X | Client FX Budget | lifetime/cap/eviction/detail for long-lived presentation | server gameplay effects |
| BCT-P | Boss Presentation | music, loops, animation cues, camera/screen effects | combat authority |

Machine-readable summary:
[toolkit-contract-v1.json](toolkit-contract-v1.json)

Detailed module contracts:
[MODULES.md](MODULES.md)

Integration policy:
[INTEGRATION-GUIDE.md](INTEGRATION-GUIDE.md)

Verification:
[VERIFICATION.md](VERIFICATION.md)

LAB stress scenarios:
[LAB-SCENARIOS.md](LAB-SCENARIOS.md)

## Mandatory cross-cutting invariants

Any adopted module must preserve these:

1. **Server gameplay authority.** Client presentation cannot decide damage,
   targeting, ownership, phase or death semantics.
2. **Bounded work.** Every scan, queue, projectile burst, destruction volume,
   retry loop and persistent visual collection has an explicit bound.
3. **Observable state.** Important attack state and cancellation/recovery reasons
   are exposed in a read-only debug snapshot.
4. **No silent vanilla leakage.** Products document which vanilla policies are
   retained, replaced or suppressed.
5. **No silent cross-target constants.** Timings, health thresholds, damage and
   ranges remain product evidence, not toolkit defaults.
6. **Data-first compatibility.** Prefer tags/config/data for target exclusions and
   compatibility seams before hard-coded foreign class checks.
7. **Semantic lifecycle before cinematics.** Presentation must not break death,
   killer attribution, loot, advancement or removal semantics.
8. **Scope-matched patching.** A standalone boss should prefer owned entity,
   renderer and projectile surfaces; global Mixins require explicit justification.

## Adoption levels

A product should record each module as:

- `NOT_USED`
- `CANDIDATE`
- `ADOPTED_CONCEPT`
- `ADOPTED_IMPLEMENTATION`

This toolkit itself does not authorize reuse of third-party code.

## Provenance

The first extraction source was the exact Wither: Reincarnated v1.0.5 artifact
described in:

- `../wither-reincarnated-boss-engineering.md`
- `../../mods/wither-reincarnated/ANALYSIS-RECEIPT-2026-10-08.json`

Additional patterns align with the existing Bedrock Wither research, especially
explicit state machines, death-lifecycle separation and read-only debug surfaces.

The source MOD is All Rights Reserved. This toolkit contains independent design
contracts only and no copied implementation/assets.

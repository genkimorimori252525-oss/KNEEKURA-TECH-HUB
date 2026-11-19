# Prior Art Review — BEStyleWither

Reviewed: 2026-10-02

Repository: MORIMORI0317/BEStyleWither  
License: LGPL-3.0  
Purpose stated by upstream: bring Wither behavior closer to Bedrock Edition.

This is a **comparative implementation reference**, not the Bedrock specification.

## Track pins

### COMPARATIVE-ANCHOR-LIKE

- branch: `1.20`
- commit: `ab98547f3e8e0dac83a814d5133a113d4bfd9e40`
- declared Minecraft: 1.20
- declared supported versions: 1.20, 1.20.1
- declared Forge: 1.20-46.0.13
- mod version: 1.6.1

This is close to, but not identical with, KNEEKURA ANCHOR 1.20.1 / Forge 47.2+.

### FRONTIER

- branch: `main`
- commit reviewed: `e658d45ea3d2b6b6b16d6a02ee6b736ce9c411d2`
- declared Minecraft: 1.21.1
- Fabric + NeoForge
- mod version: 1.8.0

## Architecture

The 1.20 implementation modifies the **vanilla `WitherBoss`** using Mixins rather than registering a standalone Bedrock-style boss.

Important surfaces:
- `WitherBossMixin`
- `WitherChargeAttackGoal`
- `WitherSkullMixin`
- renderer/model Mixins
- configuration gates for each behavior

FRONTIER later extracts transient behavior into a `WitherBossInstance` object but still patches vanilla `WitherBoss`.

## Useful implementation ideas

### Charge attack as a separate Goal

`WitherChargeAttackGoal`:
- only activates while powered
- owns target, prep/hold state and charge vector
- stops navigation while charging
- sets the vanilla destruction timer during the charge
- applies a fixed forward velocity
- has a separate cooldown

Reusable lesson: isolate charge sequencing from the base boss AI.

### Explicit second-phase persistence

The mod tracks whether the Wither has ever become weakened/powered, allowing a persistent second-phase state rather than relying solely on current health.

Reusable lesson: phase transition should be latched explicitly.

### Transition handling

The mod:
- pushes the Wither downward after half health
- waits for ground/contact conditions
- performs an explosion
- summons Wither Skeletons on Normal/Hard
- retains state so the event is not repeated

Reusable lesson: the transition is a timeline/state, not just a boolean health check.

### Dangerous skull adaptation

The mod modifies dangerous skull behavior:
- additional blue/dangerous shots
- changed inertia
- makes a dangerous skull hittable/deflectable

Reusable lesson: projectile behavior deserves its own acceptance surface.

### Death handling

The project has dedicated custom death/explosion handling and its changelog records prior fixes around Wither death compatibility.

Reusable lesson: do not overload vanilla death flow without a separate lifecycle contract and compatibility tests.

## Important differences from our target

The upstream implementation is intentionally "BE style", not demonstrated exact Bedrock parity.

Observed source differences/candidates include:

1. **Health**
   - 1.20 branch doubles the Java max-health attribute globally.
   - our target must reproduce measured difficulty-specific Bedrock health if confirmed.

2. **Skeleton count**
   - 1.20 branch normally spawns 3, with a 1/8 chance of 4.
   - FRONTIER source chooses 3 or 4 with equal probability.
   - current Bedrock reconnaissance commonly reports 3 on Normal/Hard.
   - therefore upstream count logic is not accepted as Bedrock truth.

3. **Charge timing**
   - upstream source uses constants `75` and `50`, cooldown `200`, and velocity scale `1.3`.
   - these are implementation choices; our Bedrock timing remains `TBD_MEASURE`.

4. **Vanilla AI leakage**
   - because the project patches `WitherBoss`, much of Java Wither AI remains active.
   - our target is a standalone entity so every accepted behavior can be attributed to our state machine.

5. **Half-health trigger ordering**
   - upstream uses ground/raycast/contact logic and its own timeout.
   - our target must first measure Bedrock ordering and only then choose the timeline.

## License/use rule

LGPL-3.0 permits study and reuse under its terms, but KNEEKURA should prefer **technique extraction and independent implementation** unless copying code is explicitly chosen with license compliance recorded.

No upstream source is copied into the KNEEKURA implementation by this review.

## Failure/repair leads

The upstream changelog points to:
- v1.4.1: fix related to Wither killing explosion
- v1.4.2: fix death handling that could cause issues with other mods (Issue #4)
- v1.7.0: fix where physical strength would not reach maximum when summoning

These are high-value Failure/Repair History candidates before our own lifecycle implementation.

## Design impact

The prior art strengthens, rather than weakens, the current KNEEKURA design decision:

- keep charge/destruction/projectile logic modular;
- latch transition state explicitly;
- but avoid patching vanilla `WitherBoss` as the behavioral core;
- measure Bedrock values instead of inheriting BEStyleWither's constants;
- add death/transition compatibility tests from the beginning.


## Failure/repair case: Issue #4 — delayed death broke killer semantics

Upstream report:
https://github.com/MORIMORI0317/BEStyleWither/issues/4

Repair commit reviewed:
`3c519d708fb1856f4661a3670aad36a6be9353da`

Observed history:
- the reporter described a Wither being held at 1 HP for the custom death/explosion delay;
- downstream logic checking `isDeadOrDying` at the killing hit could therefore see the boss as not dead;
- the reporter also warned that later self-driven death could lose the original killer identity for kill-dependent advancements/mods;
- the maintainer explicitly confirmed the `isDeadOrDying`/Fabric kill-event timing problem, while saying the claimed self-kill portion was not confirmed;
- the repair removed the separate "alive at 1 HP" death state, called vanilla `die`, used vanilla `deathTime`/`tickDeath` lifecycle timing, suppressed duplicate loot during the initial death call, and retained the extended visual/explosion sequence around that lifecycle;
- the original reporter subsequently confirmed their advancement triggered correctly.

Engineering lesson for KNEEKURA:
**visual death staging must not postpone the semantic death transition.** Preserve vanilla/Forge killer attribution and death-event lifecycle, then layer Bedrock-style visual/explosion timing around it. Any custom death controller needs interoperability tests for `isDeadOrDying`, kill events, loot ownership and advancement credit.

This lesson is adopted in the product ledger. It does not imply that BEStyleWither's entire repaired death implementation is copied or that every loader/event edge case is solved.

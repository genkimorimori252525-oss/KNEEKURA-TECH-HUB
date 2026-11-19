# BWR-0013 — inherited projectile paths and presentation expressions diverged

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (local GameTests / independent review)

## Symptom and root cause

Mapped Forge 1.20.1 dispatches projectile collisions through `onHit`; the custom override did not call entity-impact handling. Direct protected-method tests therefore passed while actual projectile ticks omitted impact damage, effects and owner kill healing. The inherited water branch also applied drag 0.8 despite the custom inertia getter returning 1.

Public projectile defaults specify five launch-immunity ticks; Java's inherited owner exclusion instead waited for spatial separation. Non-damaging potion impact did not call `hurt`, so the documented 1.26.0 projectile-reflection path was missing.

Pinned client JSON separately exposed literal angular expressions, floating-point modulo skin selection and two armor layers; the previous Java implementation used rounded constants, integer division and only one layer.

Basis: actual source/bytecode inspection and behavioral RED tests. No rendering or Bedrock empirical test is inferred from headless verification.

## Repair and scope

- Dispatch direct entity impact once before the custom explosion/removal path
- Preserve source-defined liquid inertia, zero gravity and timed owner grace
- Bridge non-damaging projectile impacts into the existing reflection adapter; respect Forge canceled/skipped impacts
- Evaluate literal source presentation expressions through production-used pure functions
- Render both shield layers with the declared Java texture/tint substitutes
- Keep reflection vector/speed, mounted-owner grace and texture identity explicitly labelled as Java adaptations

The eleven focused tests cover actual projectile tick/collision, kill healing, air/water travel, owner grace, immediate reflection, non-damaging impact, skipped impacts and presentation inputs. The energy-swirl shader was independently inspected and already ignores light; no unsupported claim of a previous visible lighting defect is made.

[Final completion evidence](../../evidence/source-completion-2026-10-03.json)

## Lesson

Test inherited engine dispatch and side effects, not just an overridden helper. Translate the actual expression semantics; visually plausible approximations are not literal source implementation.

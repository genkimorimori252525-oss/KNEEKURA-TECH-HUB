# BWR-0012 — ordinary combat paths were incomplete

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (local GameTests / independent review)

## Symptom and root cause

The original controller fixtures passed while ordinary phase-1 special movement and phase-2 firing/charge had no complete production entry path. Phase 2 returned from the volley controller, and dash execution was entered only by explicit test calls. Separate native aerial-height control was absent. Exact projectile observations also exposed a 140 + fireRate inter-volley delay and only nineteen physical travel steps for a twenty-count charge.

Basis: direct source and mapped Forge bytecode inspection, retained external behavior documents, and failing ordinary `ServerLevel.tickNonPassenger` tests. The original historical health-interval ledger also misdecoded signed multiply-high as /3; independently verified arithmetic is /6. This was a source interpretation correction, not a new current-native claim.

## Repair

- Connect target-relative reposition, aerial ascent, hover, both-phase volleys, alternate phase-2 charge and recovery
- Separate the selected 140-tick phase-2 projectile gap from per-shot rate
- Keep the final charge velocity through the twentieth physical movement step, then clear it
- Descend using block-only ground checks and a declared finite fallback before the one-shot transition
- Normalize transient/legacy saved states; persist the rate cursor, volley alternation and transition latch
- Reject nonfinite inputs and protected spawn/death/transition overrides
- Exclude creative/spectator targets from priority-1 selection and immediate controllers
- Permit phase-independent side-head processing outside explicit special-state gates
- Let shared firing gates expire when the main target is lost, so passive side-head firing can resume

Source choices and limits are in ADOPTION and SOURCE-AUDIT-2026-10-03.md. No empirical Bedrock measurement was performed and historical/adaptation values are not presented as current binary facts.

## Regression evidence

The first ordinary-flow RED generation failed the intended move, phase-2, target-loss, descent and reload cases while prior tests passed. Additional RED cases covered actual projectile spacing, physical charge distance, invalid adapters, rate-stage reset, player eligibility and ground-start ascent. Independent final review added transition-entry and targetless-delay regressions. Final source-bound results are in [the completion receipt](../../evidence/source-completion-2026-10-03.json).

## Lesson

A manually callable controller is not a completed behavior. Test the ordinary engine entry path, physical movement, spawned projectiles, target loss and persisted state rather than treating field counters as sufficient evidence.

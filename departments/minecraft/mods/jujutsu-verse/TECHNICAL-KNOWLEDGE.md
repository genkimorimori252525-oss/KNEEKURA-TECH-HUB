# Reusable technical knowledge

## T01 — Domain durability is its own combat resource
DOMAINHP is separate from owner health.
Invariant: arena/refinement failure should not be forced into ordinary HP.

## T02 — Contest strength can be continuous
Opposing amplifiers push/pull Domain HP every tick.
Invariant: competing fields can resolve over time rather than one winner lookup.

## T03 — Ordinary hits can feed field durability
The normal attack pipeline calls DomainbattleProcedure.
Invariant: special arena systems should have one explicit bridge from ordinary combat.

## T04 — Large spherical work should be amortized
Sure-hit and teardown use scheduled shell traversal.
Invariant: semantic simultaneity does not require CPU work in one tick.

## T05 — Cinematic presentation should observe state, not own it
DomainCutinOverlay reads domain state but does not decide the winner.
Invariant: authoritative battle logic and client cinematics evolve independently.

## T06 — Lock cinematic participants
Participant order is preserved during the cut-in.
Invariant: per-frame distance sorting should not reorder split-screen panels.

## T07 — Depth can be a lightweight panel mask
The cut-in writes depth with color disabled, then renders through it.
Invariant: non-rectangular GUI panels need not require a stencil buffer.

## T08 — Render live actors instead of portrait assets
The real LivingEntity is rendered in GUI space.
Invariant: cinematics can inherit skins/models automatically.

## T09 — Sync semantic VFX parameters, reconstruct geometry locally
Beam/VFX state is compact; trails/ribbons are client-generated.
Invariant: network state should describe an effect, not serialize every vertex/particle.

## T10 — World-anchored post effects need 3D-to-screen projection
RippleEffectManager projects the target position to shader EpiCenter.
Invariant: screen effects can remain spatially tied to world actors.

## T11 — One aura vocabulary can bridge renderer families
Vanilla and GeckoLib renderers use shared aura utilities.
Invariant: status visuals should target rendering semantics, not concrete model classes.

## T12 — Off-screen rendering creates impossible surfaces
Domain portal surfaces sample a separately rendered TextureTarget.
Invariant: portal/domain surfaces are compositing problems, not merely animated textures.

## T13 — Structured procedural geometry beats unbounded randomness
Fuga/Black Flash use geometric scaffolds plus noise.
Invariant: topology first, randomness second.

## T14 — Visual quality and performance budget are separate
The mod combines forced particles, procedural geometry, post effects and extra FBO work.
Invariant: preserve architecture but add distance/LOD/count/frame-time budgets.

## T15 — Presentation cardinality is not simulation cardinality
Three-user cut-in support coexists with pair-oriented battle state.
Invariant: document visual and simulation participant counts separately.

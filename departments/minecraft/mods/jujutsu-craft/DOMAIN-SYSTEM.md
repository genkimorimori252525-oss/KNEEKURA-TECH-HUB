# Domain system deep dive

## Common creation layer

`DomainExpansionCreateBarrierProcedure` is shared infrastructure.

It tracks:

- domain coordinates
- cover / cover count
- domain start/failure state
- attack-start state
- open-barrier mastery
- curse-energy use
- domain battle interaction

Character-specific choices are layered above this state machine.

## Active lifecycle

`DomainExpansionOnEffectActiveTickProcedure` repeatedly:

- dispatches character-specific domain active behavior
- resolves DomainExpansionBattle
- tracks health/damage/failure/defeat/target state
- coordinates cover and domain cancellation
- interacts with Simple Domain, Neutralization and special character/domain states

## Anti-domain mechanisms

The artifact distinguishes:

- Simple Domain
- Domain Amplification
- Hollow Wicker Basket
- Falling Blossom Emotion

Capability tags decide who may use several of these systems.

Domain Amplification also participates in the Infinity bypass policy.

## Malevolent Shrine

Sukuna's shrine uses the common domain radius/lifecycle but its active payload repeatedly executes area attacks and block destruction.

The implementation is best understood as an ongoing server-side attack field whose world-destruction parameters are explicit.

## Engineering extraction

A modern reusable domain engine should separate:

1. arena/barrier geometry
2. domain ownership/state
3. sure-hit / attack payload
4. anti-domain counter state
5. domain-vs-domain resolution
6. visual/animation layer

This mirrors the strongest separation already present in the artifact.

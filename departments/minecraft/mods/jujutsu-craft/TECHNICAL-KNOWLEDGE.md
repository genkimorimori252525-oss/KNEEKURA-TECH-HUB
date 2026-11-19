# Technical knowledge

## T01 — Persistent field actor instead of projectile

Blue, Red and Purple are Geo/PathfinderMob-style world entities that own position, lifetime, area queries, movement influence, damage and animation.

**Invariant:** an effect whose meaning persists over time/space can be represented by a field actor rather than a projectile packet.

## T02 — Centralized defense/counter predicate

Infinity's counters converge in `AntiInfinityProcedure`.

**Invariant:** defense rules and bypass rules should live behind one auditable predicate.

## T03 — Shared domain state machine

Domain Expansion uses common lifecycle/battle procedures plus character-specific active behavior.

**Invariant:** arena setup, battle state and anti-domain rules are infrastructure; only technique payload should vary by character.

## T04 — Per-source adaptation ledger

Mahoraga stores adaptation progress by damage-source identity in equipment NBT and uses repeated exposure to change incoming damage semantics.

**Invariant:** adaptation can be modeled as a keyed learning ledger rather than one global resistance scalar.

## T05 — Attack resolver with stochastic escalation

`RangeAttackProcedure` is reused by many techniques and can escalate a valid attack into Black Flash according to state-sensitive stochastic attempts.

**Invariant:** exceptional combat events can be layers in the common resolver rather than duplicated per technique.

## T06 — Capability-backed persistent combat state

PlayerVariables stores curse power, selected/primary/secondary techniques, costs, experience, fame, level, profession, charge and major flags.

**Invariant:** large combat systems benefit from one versioned authoritative player state contract.

## T07 — Tag-driven combat capabilities

Entity tags identify which actors may use RCT, Domain Amplification, Simple Domain, Hollow Wicker Basket and more.

**Invariant:** ability eligibility can be data-driven separately from concrete entity classes.

## T08 — Explicit anti-domain vocabulary

Simple Domain / Domain Amplification / Hollow Wicker Basket are distinct counter systems rather than one generic immunity.

**Invariant:** preserve semantic counter verbs because they compose differently with domains and Infinity.

## T09 — Separate player and GeoEntity animation paths

Players use PlayerAnimator with a custom network message; GeoEntities use GeckoLib animation APIs.

**Invariant:** different render actor types may need different animation transports but should expose a common semantic animation intent.

## T10 — Procedure graph before class-name interpretation

1,080 procedure classes make the call graph more important than filenames.

**Invariant:** generated-code projects require reachability maps and shared-helper detection before behavior classification.

## T11 — Effect topology and block interaction are explicit parameters

Area techniques feed Range, Knockback, BlockRange, BlockDamage, DomainAttack and ExtinctionBlock into shared helpers.

**Invariant:** world destruction should be a first-class effect parameter, not hidden side effects.

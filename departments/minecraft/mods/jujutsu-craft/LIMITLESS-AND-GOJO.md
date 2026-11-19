# Limitless and Gojo deep dive

## Technique dispatch

`CursedTechniqueGojoProcedure` maps persistent skill state to core Limitless techniques including Infinity, Blue, Red, Hollow Purple and Unlimited Void.

## Infinity — two enforcement layers

### 1. Spatial layer

`InfinityActiveTickProcedure` runs while Infinity is active and not neutralized. It scans nearby entities/ranged objects, maintains persistent stop/name state and alters movement so approaching threats can be slowed/stopped before contact.

### 2. Damage-event layer

`WhenEntityAttacked1Procedure` checks a living victim for `INFINITY_EFFECT`. If Infinity is active, Neutralization is absent and the Forge event is cancelable, incoming damage can be cancelled outright.

This means current 50.1 does not rely only on projectile interception.

## AntiInfinity

`AntiInfinityProcedure` centralizes bypass cases including:

- Domain Amplification
- Comedian
- effectConfirm states used by special attacks
- Inverted Spear of Heaven
- Black Rope
- Mahoraga Limitless-adaptation threshold

This is a strong reusable design: a defense system and its legal counters share one policy function.

## Blue

Blue is a persistent field actor.

`AIBlueProcedure`:

- maintains owner/ranged linkage
- changes nearby entity velocity
- performs power-scaled area attacks through `RangeAttackProcedure`
- can destroy blocks
- has a finite lifecycle

Do not model it as a vanilla arrow-style projectile.

## Red

Red is also a persistent actor.

`AIRedProcedure` gives it:

- finite active life
- power-scaled range/knockback
- a damage curve that decays over life but floors at a minimum
- movement state and area attack through the shared resolver

## Hollow Purple

`HollowPurpleProcedure` first stages Blue and Red entities with Purple flags, then creates `PurpleEntity`.

`AIPurpleProcedure` runs a moving, size-scaled damage/destruction field with particles/electric presentation and explicit block destruction. Exploded mode increases size and lifetime.

**Reusable idea:** compose earlier effect actors into a later combined technique rather than treating the final technique as unrelated code.

## ver50.1 repair boundary

The 2026-04-26 author changelog says “Fixed bug: Gojo's Limitless Technique.”

Current 50.1 clearly contains both spatial and event-level Infinity enforcement plus AntiInfinity counter policy. Without the exact ver50 class bytes, the changed branch is **NOT_ESTABLISHED**.

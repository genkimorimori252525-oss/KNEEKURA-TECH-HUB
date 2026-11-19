# Jujutsu engine pipeline — Jujutsu Craft ver50.1

Status: **ORIGINAL_BINARY static analysis / runtime NOT_RUN**

This document extracts the common execution engine underneath the large set of named techniques.

## 1. Technique identity

Technique selection is stateful, not item-driven.

The common identity is roughly:

```text
skill = technique family * 100 + selected slot
```

The player capability persists:

- selected skill slot
- selected name
- original/effective cost
- primary/secondary technique family
- passive flag
- physical-attack flag
- curse energy
- progression flags and combat state

## 2. Selection and cost normalization

`TechniqueDecideProcedure` is the common normalizer.

It stores:

- `PlayerSelectCurseTechnique`
- `PlayerSelectCurseTechniqueCost`
- `PlayerSelectCurseTechniqueCostOrgin`
- `PhysicalAttack`
- `PassiveTechnique`
- selected name / overlay strings

Shared modifiers are applied here.

This means Six Eyes/Sukuna/Star Rage economics are not duplicated in every technique Procedure.

## 3. Activation transaction

`StartCursedTechniqueProcedure` behaves like a transaction boundary.

It checks:

- whether the entity can start a technique;
- current CURSED_TECHNIQUE/COOLDOWN/UNSTABLE state;
- available curse power;
- item/skill cost rules.

On success it:

1. deducts curse energy;
2. stores composite skill identity;
3. resets counters;
4. applies CURSED_TECHNIQUE effect;
5. establishes cooldown semantics.

The technique payload starts only after this common resource/state commit.

## 4. Active technique state machine

The CURSED_TECHNIQUE MobEffect drives multi-tick execution.

`CursedTechniqueOnPotionActiveTickProcedure` and its secondary dispatcher route the stored skill to family-specific `CursedTechnique*Procedure` classes.

This lets one Z press launch a technique that continues through counters/stages over many ticks.

## 5. Semantic parameter vocabulary

Technique-specific Procedures frequently communicate with common helpers through persistent keys such as:

- `Damage`
- `Range`
- `knockback`
- effect/effect level/effect time
- `BlockRange`
- `BlockDamage`
- `ExtinctionBlock`
- `DomainAttack`
- `effectConfirm`
- target type / ranged names
- owner / OWNER_UUID

A technique can therefore be mostly “parameter preparation + helper calls.”

## 6. Target legality — LogicAttack

`LogicAttackProcedure` is the common attack-policy gate.

It handles cross-cutting relationships such as:

- ownership / OWNER_UUID;
- friendly/family state;
- betrayal-like state;
- guard / prayer-song conditions;
- target-type restrictions;
- domain target policy.

When `DomainAttack` is true, it delegates to `LogicAttackDomainProcedure`.

This is more important than any single attack's entity class because it determines whether a candidate can legally be hit.

## 7. RangeAttack — common living-target resolver

`RangeAttackProcedure` consumes the prepared semantic state.

Observed responsibilities include:

- read/normalize `Damage`;
- call `DamageFixProcedure`;
- read `Range` and `knockback`;
- enumerate nearby candidates;
- call `LogicAttackProcedure`;
- apply damage/effects/knockback;
- handle DomainAttack/effectConfirm state;
- progression/fame/experience/technique-use bookkeeping;
- stochastic Black Flash escalation.

This is the central “area technique hits living things” engine.

## 8. Black Flash as resolver escalation

Black Flash trials occur inside the shared attack resolver.

A normal valid attack can be promoted to Black Flash based on stochastic trials whose count is affected by actor/combat state.

That architecture is reusable:

```text
valid hit
  -> optional exceptional-event resolver
  -> enhanced output + presentation + progression
```

instead of requiring every melee technique to duplicate Black Flash code.

## 9. Damage normalization

`DamageFixProcedure` adjusts common Damage/knockback state before the main attack application.

Individual techniques can express intent in a consistent parameter format while shared normalization handles cross-cutting combat rules.

## 10. World destruction

`BlockDestroyAllDirectionProcedure` is the common block-effect resolver.

It consumes:

- `BlockRange`
- `BlockDamage`
- `knockback`
- `ExtinctionBlock`
- technique state/context

and performs the surrounding block mutation/destruction pass.

This is why Cleave, Purple, Malevolent Shrine, Thin Ice Breaker and other destructive techniques can share one world-interaction language.

## 11. Projectile / ranged actors

Travelling techniques create dedicated ranged actors and owner metadata.

Examples:

- ProjectileSlashEntity
- ICE_SPEAR
- ENERGY_BALL_WHITE
- NEEDLE
- METEOR
- BODY_REPEL

The actor owns motion/lifetime/visual state, but legal impact/damage still converges on shared combat policy.

## 12. Persistent field actors

Other techniques are not projectiles at all.

Examples:

- Blue
- Red
- Purple
- True Sphere
- Liquid Metal
- Domain actors

They update in the world and repeatedly prepare RangeAttack / BlockDestroy parameters.

This supports continuous force fields, aura hazards and moving areas naturally.

## 13. Effects as technique controllers

MobEffects are also first-class execution state.

Examples:

- CURSED_TECHNIQUE
- INFINITY_EFFECT
- DOMAIN_EXPANSION
- SIMPLE_DOMAIN
- DOMAIN_AMPLIFICATION
- REVERSE_CURSED_TECHNIQUE
- STAR_RAGE
- PROJECTION_SORCERY
- INSECT_ARMOR
- Instant Spirit Body-related states

Effects provide multi-tick state without requiring every technique to keep a bespoke entity alive.

## 14. Counter / neutralization layer

Cross-cutting defenses are shared policies/effects:

- Infinity + AntiInfinity
- Guard
- Neutralization
- Simple Domain
- Domain Amplification
- Hollow Wicker Basket
- Falling Blossom Emotion
- Mahoraga adaptation

The best design property is that counter semantics are usually queried by common gates rather than copied into every technique.

## 15. Domain pipeline

Domain Expansion runs as a parallel shared subsystem:

```text
technique dispatch
 -> DomainExpansionCreateBarrier
 -> center / mode / build counters
 -> GetDomainBlock palette
 -> DomainExpansionBattle reversible geometry
 -> DOMAIN_EXPANSION effect
 -> character-specific DomainActive payload
 -> DomainAttack target policy
 -> clash/counter state
 -> teardown / old_block restoration
```

Open-type mode changes the geometry branch itself rather than only setting a visual flag.

## 16. Persistent player/world state

`PlayerVariables` is the authoritative per-player state plane.

It includes curse energy, selected techniques, progression, Six Eyes/Sukuna/physical/passive state and UI/charge information.

`WorldVariables` / map variables hold shared state such as DomainExpansionRadius.

This makes technique execution reproducible across ticks and network boundaries.

## 17. Animation and network presentation

Semantic combat state is separate from animation transport.

### Player actors

PlayerAnimator:

- ModifierLayer
- custom message with animation name/entity ID/override
- client resolves target player and starts keyframe animation

### GeckoLib actors

GeoEntities use their Gecko animation controllers / `setAnimation(String)` helper paths.

The technique engine asks for animation intent while player/entity rendering uses separate transports.

## 18. Full execution pipeline

The current architecture can be summarized as:

```text
INPUT
  R / Z / other keys
    ↓
SELECTION
  TechniqueDecide
  cost normalization
    ↓
TRANSACTION
  StartCursedTechnique
  curse-energy deduction
  cooldown / skill state
    ↓
STATE MACHINE
  CURSED_TECHNIQUE effect
  family dispatch
    ↓
PAYLOAD
  semantic parameters
  dedicated projectile / field / summon / effect
    ↓
POLICY
  LogicAttack
  Infinity / guard / ownership
  DomainAttack / anti-domain
    ↓
OUTPUT
  RangeAttack
  BlockDestroyAllDirection
  movement / effects / summon state
    ↓
PRESENTATION
  particles / sounds / Gecko / PlayerAnimator / packets
    ↓
CLEANUP
  counters / cooldown / entity lifetime / domain restoration
```

## 19. Reusable design lessons

1. **Centralize resource transaction before technique execution.**
2. **Use semantic parameters to share hit/block logic across many skills.**
3. **Represent persistent spatial techniques as actors, not fake projectiles.**
4. **Make target legality a policy layer independent from delivery mechanism.**
5. **Keep defense and bypass predicates centralized.**
6. **Treat domains as reversible world overlays with separate payload logic.**
7. **Let exceptional combat events such as Black Flash be resolver extensions.**
8. **Keep animation transport downstream from combat semantics.**
9. **Use stable data/tag capability membership instead of hard-coding every entity class.**
10. **In generated-code projects, reason from the helper/call graph rather than class count.**

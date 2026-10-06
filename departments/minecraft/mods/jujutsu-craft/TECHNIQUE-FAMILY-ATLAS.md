# Technique family atlas — Jujutsu Craft ver50.1

Status: **ORIGINAL_BINARY static analysis / runtime NOT_RUN**

This document maps representative technique families from the exact ver50.1 ANCHOR to their shared activation contract and live implementation style.

The mod contains roughly 210 selectable family/slot branches in the generated technique-selection procedures. This atlas only publishes entries whose family dispatch/call path was rechecked; automated name extraction is not treated as authority by itself.

## Shared activation contract

Player technique use follows the same broad transaction:

```text
R / technique selection
  -> TechniqueDecideProcedure
     -> selected skill/name/cost/passive/physical state
Z / start
  -> StartCursedTechniqueProcedure
     -> eligibility
     -> curse-energy check
     -> cost deduction
     -> skill = family*100 + slot
     -> reset counters
     -> CURSED_TECHNIQUE effect
CURSED_TECHNIQUE tick
  -> family-specific CursedTechnique*Procedure
     -> dedicated actor/effect OR shared RangeAttack/BlockDestroy
     -> animation / sync
     -> cooldown / cleanup
```

### Common cost modifiers

- **Six Eyes:** effective cost is multiplied by `0.1^(amplifier+1)`, then rounded.
- **Sukuna Effect:** cost is multiplied by 0.5.
- **Star Rage:** physical-attack costs are increased by its current state.
- **Cursed Speech Loudspeaker:** equipment/context can alter its cost path.

Cost normalization happens before the family payload, so technique implementations do not each own their own Six-Eyes/Sukuna formulas.

## Gojo / Limitless

| Skill | ID | Base cost | Implementation style |
|---|---:|---:|---|
| Infinity | 205 | 0 | persistent defensive effect + event cancellation |
| Blue | 206 | 200 | persistent moving attraction/area actor |
| Red | 207 | 500 | persistent repulsive area actor |
| Blue Strike | 208 | 200 | physical / area hybrid |
| Hollow Purple | 215 | 1000 | staged Blue+Red -> Purple persistent destructive actor |
| Unlimited Void | 220 | 1250 | shared Domain Expansion engine |

Infinity is not just a projectile filter: spatial interception and event-level damage cancellation both exist, and bypasses are centralized in `AntiInfinityProcedure`.

Blue/Red/Purple use world actors rather than arrow-like projectiles, allowing them to own lifetime, motion, area queries, block interaction and Gecko animation.

## Sukuna

| Skill | ID | Base cost | Implementation style |
|---|---:|---:|---|
| Dismantle | 105 | 100 | `ProjectileSlashEntity` ranged slash |
| Cleave | 106 | 200 | immediate shared RangeAttack + block destruction |
| Divine Flame / Open | 107 | 1000 | staged fire technique |
| Malevolent Shrine | 120 | 1250 | open-capable domain + repeated area/block attack |

Dismantle and Cleave intentionally use different effect topologies: one is a travelling slash actor, the other is closer to a spatial volume operation.

Malevolent Shrine repeatedly executes common attack and world-destruction helpers under DomainAttack semantics.

## Cursed Speech / Inumaki

Representative skills:

- 305 Explode — 400
- 306 Get Crushed — 250
- 307 Crumble Away — 500
- 308 Don't Move — 150
- 309 Blast Away — 300
- 320 domain — 1000

One `CursedSpeechProcedure` interprets the selected skill and feeds different damage/knockback/effect parameters to shared `RangeAttackProcedure`.

The words are therefore semantic presets over one common execution engine, not unrelated projectile classes.

## Jogo / Disaster Flames

Representative skills:

- 405 Disaster Flames — 180
- 406 Burned Out — 120
- 407 Ember Insects — 150
- 408 Flame Laser — 150
- 409 Lava Flow — 500
- 415 Maximum Meteor — 1250
- 420 Coffin of the Iron Mountain — 1250

The family mixes:

- direct area attack + block destruction;
- moving energy actors;
- Ember Insect actors;
- dedicated Meteor ranged actor;
- shared domain infrastructure.

This is a good example of one technique family selecting different physical representations by effect meaning.

## Ten Shadows / Megumi

`TenShadowsTechniqueProcedure` is primarily a summon/state manager.

Summons include:

- Divine Dogs
- Nue
- Max Elephant
- Rabbit Escape
- Great Serpent
- Toad
- Piercing Ox
- Round Deer
- Tiger Funeral
- Agito
- Mahoraga

They share ownership state such as `OWNER_UUID`, friendly counters and despawn/return logic.

Chimera Shadow Garden uses domain ID **6** and dedicated domain actors, while shikigami remain independent owned combat entities.

## Blood Manipulation / Choso

Representative verified skills:

- Slicing Exorcism — 1005 / 120
- Convergence — 1006 / 25
- Piercing Blood — 1007 / 200
- Supernova — 1008 / 100
- Flowing Red Scale — 1009 / 100
- Blood Waves — 1016 / 400
- domain — 1020 / 1250

The family separates:

- **preparation state** — Convergence;
- **directed line/range attack** — Piercing Blood;
- **staged detonation** — Supernova;
- **self MobEffect** — Flowing Red Scale;
- **dedicated projectile actor** — Slicing Exorcism.

## Mahito / Idle Transfiguration

Representative verified paths include:

- Idle Transfiguration — 1505 / 100
- body-repel family — 1507–1509
- Soul Multiplicity — 1510 / 200
- Instant Spirit Body — 1515 / 500
- slash / transformed combat — 1516
- Self-Embodiment of Perfection — 1520 / 1250

Implementation styles are deliberately separate:

- target transfiguration via immediate attack/effect-confirm path;
- Body Repel ranged actors;
- Polymorphic Soul Isomer owned summons;
- Instant Spirit Body self-transform effect;
- domain ID **15**.

## Mahoraga

Representative skills:

- Air Cannon — 1607 / 250
- Car Throwing — 1608 / 150
- Strong Overhead — 1615 / 300
- World-cut — 1619 / 500

Mahoraga's defining mechanic is not these attacks alone but the adaptation ledger:

- generic adaptation keyed by damage-source identity;
- separate Limitless-specific `skill205` progress;
- environmental completion responses;
- attack/state changes tied to adaptation.

## Projection Sorcery / Naoya

Representative skills:

- Top Speed Punch — 1907 / 300
- Air Freeze — 1910 / 125
- Time Cell Moon Palace — domain ID 19

Key building blocks:

- `ENTITY_PROJECTION_SORCERY` controller;
- `PROJECTION_SORCERY` state;
- high-speed movement/collision logic;
- `SpeedIsPower` translating velocity state into damage, knockback and block destruction.

The combat resource here is **kinematic state**, not only curse energy.

## Cursed Spirit Manipulation / Geto-Kenjaku

The family treats captured curses as an owned resource pool:

- curse grade/count state;
- `OWNER_UUID`;
- owned curse spawning/despawning;
- Uzumaki actor;
- Mini-Uzumaki shared RangeAttack + block-destruction output.

Womb Profusion uses domain ID **18** and is one of the open-barrier-capable domain routes.

## Todo / Boogie Woogie

Boogie Woogie is a positional-control technique.

It validates target/ownership/guard/domain-related state, then explicitly rewrites both participants' positions.

The technique's core verb is:

```text
SWAP(actorA, actorB)
```

rather than damage.

Separate Todo attack paths include Lariat and a dedicated Black Flash route.

## Yuki / Star Rage

Star Rage is a self/combat-state effect and is also read by the common cost resolver, where it increases physical-attack cost.

The family includes:

- enhanced physical attacks;
- Garuda owned actor / projectile form;
- progression into a `BLACK_HOLE` actor;
- Tsukumo domain ID **9**.

This is an example of one MobEffect modifying both combat output and resource economics.

## Hakari

Idle Death Gamble uses domain ID **29**.

The family also uses:

- Reserve Ball;
- Doors;
- Consecutive Effects;
- jackpot/domain state.

The shared domain builder gives ID29 a **10-block shell thickness**, unlike the normal 1-block shell, so technique rules feed back into arena geometry.

## Higuruma

Deadly Sentencing uses domain ID **27** and coordinates:

- `JUDGEMAN`;
- guillotine/gavel infrastructure;
- adjudication state;
- later weapon/judgement consequences.

The common domain engine owns the physical barrier, while Judgeman/domain state owns the trial semantics.

## Ishigori

Granite Blast exists in two useful topologies:

1. direct beam-like RangeAttack;
2. a variant that also creates `ENERGY_BALL_WHITE` as a moving ranged actor.

His domain uses ID **12**.

This demonstrates that an identical fiction/name can have multiple physical delivery mechanisms inside one family.

## Uro

Thin Ice Breaker:

- creates `ENTITY_CRACK`;
- emits broken-glass presentation;
- performs RangeAttack;
- applies knockback;
- calls block destruction;
- interacts with Uro counter/guard state.

Uro's domain uses ID **38**.

## Yorozu

The family is built around persistent material state.

- Liquid Metal creates/reuses a `LIQUID_METAL` actor identified by UUID.
- Liquid Arrow derives from that material state.
- Needle creates a dedicated ranged actor.
- Insect Armor is a self MobEffect.
- True Sphere is a persistent `TRUE_SPHERE` actor.
- Threefold Affliction is domain ID **39**.

This is a strong reusable architecture: **material controller -> multiple derived techniques**.

## Angel

Jacob's Ladder uses a dedicated marker/circle actor and target/height/distance logic rather than a plain projectile.

Angel's domain uses ID **28** and a dedicated temple presentation.

## Kaori / Anti-Gravity

Normal anti-gravity is built from direct RangeAttack/knockback semantics.

Reversed anti-gravity adds block destruction and reverses/changes the force semantics.

This is a clean normal/reversal pairing over shared spatial helpers.

## Uraume

Representative verified skills:

- Ice Spear — 2405 / 50
- Frozen — 2406 / 120
- Frost Calm — 2408 / 250
- Icefall — 2409 / 300
- generic family domain — 2420 / 1250

The family uses:

- `ICE_SPEAR` / `ICE_SPEAR_2` actors;
- shared RangeAttack;
- `BlockToIceProcedure` for world mutation.

Freezing the arena is part of the payload, not merely a status effect.

## Nanami / Hanami / Ino / Kugisaki

These families expose more shared technique forms:

- **Nanami:** melee-special state plus Collapse/Garagara block fragmentation.
- **Hanami:** root/spear/ball actors plus Flower Offering world/area interaction.
- **Ino:** summon/effect forms Kaichi, Reiki, Kirin and Ryu.
- **Kugisaki:** Hairpin uses shared RangeAttack + block destruction; Nail uses hammer/nail equipment state; domain ID34.

## Black Flash

Black Flash is not fundamentally a family-specific skill.

It is embedded in the common `RangeAttackProcedure` as a stochastic escalation of a valid attack. Character/state conditions can increase the number of trials; each observed trial is approximately `Math.random() > 0.998`.

On success the common pipeline creates Black Flash effects/entities/sounds/progression.

## Reverse Cursed Technique

RCT is effect-driven and uses shared curse-power accounting.

Its active path considers:

- self/outward use;
- fatigue;
- target type;
- cursed-spirit polarity;
- curse-energy cost.

The exact player-facing heal rate remains runtime NOT_RUN.

## Common family grammar

Across these techniques the recurring implementation grammar is:

```text
family/skill dispatch
  -> set semantic parameters
     Damage / Range / knockback / effects
     BlockRange / BlockDamage / ExtinctionBlock
  -> optional dedicated actor
  -> LogicAttack
  -> RangeAttack
  -> optional BlockDestroyAllDirection
  -> counter/domain policy
  -> animation + network presentation
```

The mod's apparent technique diversity is achieved mostly by recombining this shared vocabulary with a smaller number of dedicated world actors.

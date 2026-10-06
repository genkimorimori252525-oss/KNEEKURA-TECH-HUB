# Sukuna combat deep dive

## Dispatch

Core technique state maps at least:

- 105 Dismantle
- 106 Cleave
- 107 Open
- 120 Malevolent Shrine

Other IDs route to combo/alternate techniques.

## Dismantle

`DismantleProcedure` uses a dedicated `ProjectileSlashEntity`.

The path carries ranged-owner/mode state and supports special world-cut / Infinity-aware conditions.

This is the more projectile-like slash route.

## Cleave

`CleaveProcedure` leans on shared:

- `RangeAttackProcedure`
- `DamageFixProcedure`
- `BlockDestroyAllDirectionProcedure`

It is closer to an immediate spatial slash/volume operation than a free-flying projectile.

## Malevolent Shrine

Creation uses shared domain infrastructure.

The active shrine repeatedly sets attack parameters and invokes area attack + world destruction.

Important parameters include:

- Damage
- Range
- Knockback
- DomainAttack
- ExtinctionBlock
- BlockRange
- BlockDamage

This is an explicit world-destructive field effect.

## World-cut lineage

Mahoraga/world-cut procedures and Sukuna state/advancement gates interact rather than implementing world cut as one isolated projectile class.

**Engineering lesson:** progression-derived techniques may be better represented as changes to attack semantics and eligibility than as separate weapon items.

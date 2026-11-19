# Boss Combat Toolkit v1 — Integration Guide

The toolkit is a menu of contracts, not a required framework.

## 1. Start from product requirements

Before selecting modules, write the boss-specific facts:

- target Minecraft/loader;
- owned EntityType or vanilla overhaul;
- attack list;
- movement model;
- phase model;
- projectile types;
- world-edit behavior;
- minion/faction behavior;
- presentation requirements;
- evidence source for each gameplay constant.

Then select toolkit modules only where they simplify those facts.

## 2. Recommended dependency direction

```text
product BossState / evidence-owned constants
             |
             +--> BCT-A attack orchestration
             |       +--> product attack implementations
             |
             +--> BCT-B beam geometry contract
             +--> BCT-D projectile ownership contract
             +--> BCT-F temporary faction contract
             |
             +--> semantic client messages
                         |
                         +--> BCT-X FX budgets
                         +--> BCT-P presentation
```

BCT-P and BCT-X must not call back into gameplay authority.

## 3. Standalone custom boss default

For a KNEEKURA-owned boss, prefer:

- custom EntityType;
- custom synced data;
- product-owned state machine/controllers;
- product-owned projectile EntityTypes where semantics differ from vanilla;
- custom renderer/model registration;
- targeted events/capabilities only where needed.

Use Mixins only for a specific platform seam that cannot be reached safely through
owned classes/events.

## 4. Vanilla-overhaul product

If the explicit product goal is to replace vanilla behavior globally, broader
Mixins may be justified.

Before patching a vanilla class, record:

- exact method/field target;
- why subclass/owned entity/event hook is insufficient;
- other mods likely to patch the same surface;
- failure behavior when the injection misses;
- version/mapping sensitivity;
- rollback or feature-disable path.

## 5. Legacy-policy checklist

Before replacing any vanilla behavior, create a table:

| Policy | Keep | Replace | Suppress | Evidence/test |
|---|---|---|---|---|
| target selection | | | | |
| movement/navigation | | | | |
| direct damage | | | | |
| projectile damage | | | | |
| healing/regen | | | | |
| invulnerability | | | | |
| block destruction | | | | |
| loot/XP | | | | |
| semantic death | | | | |
| visual death | | | | |
| boss bar | | | | |
| sound/music | | | | |
| renderer/model | | | | |

No row may be implicitly "whatever vanilla happens to do".

## 6. Numeric constants

Toolkit docs intentionally contain no required:

- HP;
- phase threshold;
- damage;
- range;
- cooldown;
- speed;
- duration;
- particle count.

A product must label each value with provenance such as:

- official specification;
- exact source/bytecode;
- direct runtime measurement;
- product design choice;
- provisional/TBD.

## 7. Networking rule

Define messages around semantics, not rendering implementation.

Good:

- attack started;
- beam direction/length;
- projectile was deflected;
- faction owner changed;
- camera impulse;
- phase presentation changed.

Avoid:

- one packet per particle;
- one packet per beam sample;
- sending complete renderer/model state;
- client commands that decide server damage.

## 8. Failure behavior

Each adopted module must define safe behavior when:

- target disappears;
- boss unloads;
- owner/minion changes dimension;
- packet arrives late/out of order;
- client does not support optional presentation;
- attack is interrupted;
- server lags;
- config disables the module mid-reload where supported;
- another mod cancels damage/block destruction.

Prefer cancellation/recovery over infinite retry.

## 9. Adoption record template

```text
Module: BCT-?
Status: CANDIDATE / ADOPTED_CONCEPT / ADOPTED_IMPLEMENTATION
Product:
Reason:
Product-owned implementation:
Evidence source:
Constants source:
Compatibility risks:
Verification IDs:
Not adopted from reference:
```

## 10. Stop condition

Do not create a shared Java runtime library merely because two bosses use the same
concept.

Promote to shared implementation only when:

1. at least two real products use the same stable semantics;
2. duplicated code is materially costly or defect-prone;
3. both products can accept the same lifecycle/API;
4. extracting it does not force gameplay constants or inheritance;
5. tests cover both adopters.

Until then, this toolkit remains the shared **contract**, with product-owned code.

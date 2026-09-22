# Twilight Forest — AI Portability Matrix v1

Source tracks:

- ANCHOR: `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625` — Minecraft 1.20.1 / Forge
- FRONTIER: `TeamTwilight/twilightforest@793c4d4c7b0a2892f702cbb9a8d751fbe7218828` — Minecraft 26.1.2 / NeoForge

## Whole AI/entity path delta

Across Java files under `entity/ai`, `entity/monster`, `entity/passive`, and `entity/boss`:

- 132 unique paths
- 111 changed
- 15 added
- 6 byte-identical
- 0 removed

This is an evolutionary lineage rather than a replacement of the old AI surface.

## Catalog completion

The FRONTIER catalog now covers:

- all **53** non-boss monster/passive classes;
- inheritance and imperative-behavior false negatives for those 53 classes;
- all **43** custom classes directly under `entity/ai/goal`;
- all eight principal boss controllers and their verified transition models.

The previous “resolve inherited/imperative behavior” item is therefore complete.

## Main portability result

The strongest recurring FRONTIER change is **behavioral decoupling**:

```text
ANCHOR
specialized boss extends another gameplay mob
+ owns home/bossbar state itself

        ↓ FRONTIER

BaseTFBoss
+ explicit reusable Goals/interfaces
+ encounter-specific state only
```

### Very high-value examples

**Ur-Ghast**

ANCHOR inherits `CarminiteGhastguard`. FRONTIER instead extends `BaseTFBoss` and explicitly composes `UrGhastFlightGoal`, `UrGhastAttackGoal`, and `UrGhastLookGoal`. The tantrum/damage-budget encounter concept survives.

**Minoshroom**

ANCHOR inherits `Minotaur`. FRONTIER extends `BaseTFBoss`, implements `ITFCharger`, and explicitly composes Float / GroundAttack / Charge / Melee / restriction / wander / look / target policies. This is a direct example of replacing behavior-by-inheritance with behavior-by-composition.

## Stable boss encounter concepts

The following core control models remain recognizable across both tracks:

- Naga — arena-constrained Goal scheduler + health-driven multipart body
- Lich — phase-gated Goals
- Hydra — authoritative coordinator + local head state machines
- Snow Queen — explicit phase enum + phase-specific Goals
- Alpha Yeti — rampage → tired/recovery cycle
- Knight Phantom — shared formation controller
- Ur-Ghast — damage-budget tantrum switching
- Minoshroom — ground slam plus charge/melee action composition

That means these concepts are strong 1.20.1 backport candidates even when the FRONTIER API syntax is unusable directly.

## BaseTFBoss

FRONTIER adds `BaseTFBoss` and dedicated boss-bar infrastructure. Naga, Lich, Hydra, Ur-Ghast, Snow Queen, Alpha Yeti, Knight Phantom, and Minoshroom all converge on this common base.

For KNEEKURA 1.20.1, the useful technology is not the modern class API itself. It is the separation:

- common boss bar lifecycle;
- common home/structure restriction;
- common death/loot lifecycle;
- encounter-specific AI left in each boss.

## Backport rule

Do not port by copying FRONTIER inheritance trees. Port in this order:

1. identify encounter invariants;
2. create ANCHOR-compatible shared boss infrastructure;
3. extract reusable action Goals/interfaces;
4. preserve authoritative phase/FSM state;
5. re-bind only presentation state to 1.20.1 networking/entity-data APIs;
6. regression-test encounter transitions against the ANCHOR behavior.

Machine-readable detail is in `AI-PORTABILITY-MATRIX.json`.

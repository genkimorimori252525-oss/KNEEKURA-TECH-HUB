# Wither: Reincarnated — Technique Harvest

Purpose: convert exact-binary findings into **portable engineering concepts** for
KNEEKURA without copying ARR code/assets.

Source receipt:
[ANALYSIS-RECEIPT-2026-10-08.json](ANALYSIS-RECEIPT-2026-10-08.json)

Cross-target version:
[../../techniques/wither-reincarnated-boss-engineering.md](../../techniques/wither-reincarnated-boss-engineering.md)

Normalized reusable contract:
[Boss Combat Toolkit v1](../../techniques/boss-combat-toolkit/README.md)

## Harvest matrix

| Technique | Evidence in target | Portable concept | KNEEKURA posture |
|---|---|---|---|
| major attack = independent Goal | Charge/Laser/Barrage/Ranged classes | explicit attack lifecycle and arbitration | ADOPT CONCEPT |
| health-gated eligibility | player targeting + charge + powered state | thresholds gate states/actions, not one giant tick | ADOPT CONCEPT |
| charge prepare/execute/recover | `WitherChargeGoal` | lock attack intent before movement; bounded recovery | ADOPT CONCEPT |
| server beam/client render | `WitherLaserGoal` + laser packets | authoritative ray hit + compact visual sync | ADOPT CONCEPT |
| projectile owner transfer | dangerous skull hit path | reflect by changing allegiance, not only direction | ADOPT CONCEPT |
| temporary faction overlay | PossessedCapability + possessed Goals | attach owner/team/time state to existing mobs | ADOPT CONCEPT with narrower attachment scope |
| tag-based exclusions | three entity tags + biome tag | compatibility exceptions should be data-driven | ADOPT CONCEPT |
| compact client event protocol | six S2C packets | send minimal state/event, derive visuals locally | ADOPT CONCEPT |
| persistent FX budgets | SmokeColumn/DistantFire caps | finite queues + lifetime + detail controls | ADOPT CONCEPT |
| barrage FX aggregation | camera-shake handling | bound visual response to event storms | ADOPT CONCEPT |
| music/audio FSM | fight state → music/loop choice | explicit presentation priority/state | ADOPT CONCEPT |
| global vanilla Mixins | WitherBoss/WitherSkull/client Mixins | suitable for overhaul, risky for standalone entity | DO NOT GENERALIZE |
| broad Living renderer injection | PossessedLayer | necessary only for arbitrary third-party entities | USE ONLY WHEN REQUIRED |
| all-Mob capability attachment | possession provider | flexible but unnecessarily broad for many products | PREFER NARROWER OWNERSHIP |
| Reincarnated timers/damage | configs/bytecode | target-specific encounter tuning | REJECT AS GENERIC/Bedrock EVIDENCE |
| assets/render implementation | ARR JAR | none without separate permission | DO NOT COPY |

## H1 — Attack arbitration should be visible

A boss with several expensive attacks needs an explicit arbitration layer.
Independent Goals naturally expose:

- eligibility;
- mutual exclusion/flags;
- start;
- continue;
- per-tick work;
- stop/recovery;
- cooldown.

Even when KNEEKURA uses a custom state machine instead of Minecraft GoalSelector,
these fields should remain observable in debug snapshots.

## H2 — Separate mechanics from presentation

A repeated pattern in this target is:

```text
server decides -> packet states/event -> client renders/sounds
```

That boundary should be preserved for beams, cinematics, boss HUD, camera shake and
persistent environmental visuals.

## H3 — Transfer ownership when an attack changes sides

Deflection is fundamentally a change in **authority/allegiance**, not just
trajectory.

A generic projectile contract should expose:

- owner/attacker identity;
- team/friendly-fire semantics;
- deflection eligibility;
- deflection velocity;
- post-deflection collision grace/assist policy;
- damage policy after ownership transfer.

## H4 — Temporary faction state is reusable

Possession shows that an existing mob can temporarily join a boss encounter
without replacing its EntityType.

Portable state:

```text
controller/owner
start tick
expiry tick
cooldown
team relationship
AI overlay
presentation state
```

KNEEKURA should prefer a narrowly scoped component/capability/data attachment
instead of attaching unused state to every Mob when the target set is known.

## H5 — Compatibility belongs in data where possible

Tags are a stable seam for:

- cannot possess;
- will not attack;
- will not flee;
- unsuitable travel biomes.

The same principle generalizes to:

- untargetable entities;
- destruction-resistant blocks;
- immune projectile targets;
- excluded dimensions/biomes;
- AI donor/receiver categories.

Hard-coded mod-class checks should be the fallback, not the first design.

## H6 — FX need budgets independent of gameplay

Client presentation must not be able to accumulate forever because a server attack
is valid.

Every persistent FX family should define:

- maximum live records;
- lifetime;
- eviction policy;
- detail level;
- disable switch;
- distance/visibility rules.

This belongs in acceptance criteria for large boss attacks.

## H7 — Stress-test the rare attack, not only normal combat

The highest performance risk can be the least frequent move.

For this target, relevant synthetic scenarios include:

- maximum-length active laser;
- dense local mob population during possession scans;
- repeated terrain interaction;
- full uninterrupted barrage;
- multiple simultaneous Withers;
- several clients in the same dimension;
- clients inside/outside visual range.

KNEEKURA LAB should measure these as separate work units instead of averaging them
into a normal-fight TPS result.

## H8 — Global overhaul architecture is not standalone-boss architecture

Wither: Reincarnated legitimately patches vanilla classes because its product goal
is to replace the vanilla Wither experience.

A KNEEKURA standalone boss should not inherit that decision automatically.

Prefer:

- owned EntityType;
- owned renderer/model;
- owned synced data;
- isolated controller/state machine;
- small compatibility hooks;

before considering global Wither/Projectile/LivingRenderer Mixins.

## H9 — Replacing a policy requires neutralizing the old policy

The lifesteal path illustrates a general repair rule: if a new global mechanic
supersedes vanilla behavior, leave no hidden legacy source that silently stacks.

Before adopting a replacement policy, inventory:

- vanilla heal;
- vanilla damage;
- vanilla drop;
- vanilla cooldown;
- vanilla target selection;
- vanilla death lifecycle;

and explicitly decide keep/replace/suppress for each.

## Adoption boundary

Everything above is a **concept** extracted from static observation of an ARR
binary. It is not permission to copy implementation.

For Bedrock reconstruction, only the engineering shape may be useful. All Bedrock
timings, thresholds, projectile values and state ordering must continue to come
from Bedrock-specific evidence.

# Boss Combat State Machines and Lifecycle Boundaries

Status: RESEARCH / REUSABLE TECHNIQUE NOTE  
ANCHOR interest: Minecraft 1.20.1 / Forge  
Initial extraction: Bedrock Wither reconstruction, 2026-10-02

Primary research context:
- `departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/`
- focused BEStyleWither review pinned there
- Java 1.20.1 Wither used as comparison/reference

These are reusable patterns, not claims that every boss should use the same constants.

## T1 — separate phase state from health predicate

Pattern:
- health threshold detects a transition;
- an explicit latch/state records that it happened;
- transition actions execute once;
- later healing does not accidentally replay or erase the phase unless the design explicitly allows it.

Why it matters:
A raw `health <= threshold` condition is insufficient for explosions, summons, one-time cinematics and persistence.

Observed prior art:
BEStyleWither separately persisted whether the weakened/half-health transition had occurred. KNEEKURA adopts the invariant concept, not its exact state fields/constants.

Transfer:
Useful for multi-phase bosses, enrages, transformations and one-shot arena events.

## T2 — isolate charge/dash sequencing

Pattern:
- preparation/acquire target;
- lock or snapshot aim/vector;
- charge execution;
- bounded timeout/collision termination;
- recovery/cooldown;
- block destruction is a separate controller/service, not an implicit side effect of generic movement.

Observed prior art:
BEStyleWither implements charge as a distinct Goal with its own target, hold interval, movement vector and cooldown.

Transfer:
Useful for giant mobs, ramming attacks, lunges and scripted movement.

Risk:
Do not copy timing/speed values across mobs or versions. Unbounded per-tick destruction can become a severe tick/loot-generation problem.

## T3 — semantic death and visual death are separate concerns

Pattern:
1. the killing hit enters the platform's normal semantic death lifecycle;
2. killer attribution, death events, advancement/loot semantics remain intact;
3. an extended visual/explosion sequence is layered around `deathTime/tickDeath` or equivalent lifecycle hooks;
4. removal timing may be delayed, but "alive at 1 HP" must not be used merely to keep a cinematic running.

Failure evidence:
BEStyleWither Issue #4 reported broken downstream kill checks when the Wither was intentionally kept alive for delayed death. The maintainer confirmed incorrect `isDeadOrDying`/kill-event timing and repaired the implementation toward the vanilla death lifecycle. The reporter then confirmed their advancement worked.

Transfer:
High-value compatibility rule for every custom boss death cinematic.

## T4 — keep projectile policy independent from boss cadence

Pattern:
- boss controller decides when/which projectile to spawn;
- projectile class owns flight/collision/deflection mechanics;
- visual distinction is synchronized separately.

Why:
This lets a boss change burst order without rewriting projectile physics and lets projectile fixes avoid disturbing target selection.

Prior art:
BEStyleWither separately modifies dangerous Wither Skull inertia/deflection while also changing boss shooting behavior.

## T5 — preserve multiple interpretations until evidence chooses one

Pattern:
When external documentation names a concept but its exact aggregation is ambiguous, store enough information to support competing interpretations.

Current example:
Bedrock's `wither_target_highest_damage` proves a highest-damage targeting concept, but public material may not completely settle whether a particular implementation should rank cumulative damage, strongest hit, or another bounded measure. KNEEKURA's initial threat ledger therefore retains both cumulative and max-single-hit data and makes selection policy explicit.

Transfer:
Useful whenever a closed implementation exposes intent but not complete algorithmic detail.

## T6 — debug state is a read-only product surface

Pattern:
Expose current phase, phase age, targets, attack counters, movement vector and destruction summary as a read-only snapshot.

Benefits:
- Tank/runtime comparisons do not need to infer every state from screenshots;
- failures become reproducible;
- changing observation code need not grant control authority.

Risk:
Debug exposure must not become a hidden gameplay command API.

## Product adoption

The first adopter is:
`deliverables/minecraft/bedrock-wither/ADOPTION.md`

Future products should link individual techniques rather than copying the entire Wither architecture.


## T7 — derive destruction volumes from entity AABB + native range

Pattern:
- preserve the entity's authoritative collision box;
- preserve an observed/native integer expansion range;
- derive candidate block coordinates from the expanded AABB instead of hardcoding a visually reported cuboid.

Bedrock Wither example:
- official collision box = 1×3
- historical/native hurt range = 1 -> inclusive 4×6×4 block positions
- historical/native charge range = 2 -> inclusive 6×8×6 block positions
- current runtime observation independently matches those dimensions.

Why this is better than hardcoding `4×6×4`:
- if entity position/alignment or dimensions change, the geometry remains structurally tied to the boss;
- the implementation can reproduce the observed northwest-of-center alignment naturally from floor/inclusive coordinate conversion;
- the same controller can retain attack-type metadata even where block exclusions differ by attack.

Transfer:
useful for ramming bosses, large mobs and native-code reconstructions where evidence exposes an AABB plus an expansion/range parameter.


## T8 — exposed component values may be native-overridden

Pattern:
- treat public entity/component JSON as an exposed configuration layer, not automatically as the final runtime value;
- search native structure/body evidence for hardcoded reload/initialization;
- compare the resulting runtime value against current observation;
- preserve both the exposed value and the effective value in the evidence record.

Bedrock Wither example:
- current Mojang JSON exposes health 600 for all difficulties;
- historical Bedrock native hardcoded reload applies 50% max-health cap on Easy and 75% on Normal, leaving Hard at 600;
- current gameplay observation independently reports 300 / 450 / 600;
- current Mojang JSON exposes movement 0.25;
- historical Bedrock native hardcoded reload sets runtime movement speed 0.6;
- current gameplay documentation independently reports speed 0.6.

Engineering lesson:
**JSON parity is not runtime parity for entities with documented unique/native behavior.**

Transfer:
This applies to future Bedrock-to-Java reconstructions, especially bosses or legacy entities with native code paths. A generated behavior pack is necessary evidence but not sufficient evidence for final runtime constants.

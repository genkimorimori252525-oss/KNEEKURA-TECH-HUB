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

# QB-MOD 1.6.4.082 — Witch ecology, familiar evolution and servant behaviors

Primary evidence: supplied QB source snapshot.

One of the least obvious systems in QB-MOD is that many “minor mobs” form a time- and kill-driven ecology rather than a static list of minions.

## EntityMajo age clock

Every `EntityMajo` has:
- `age`;
- `summonServant` counter.

Each living update:
1. `age++`;
2. if `age > canAdvance()`, attempt to replace the entity with `getAdvance()`;
3. if `age > getNextSummonTime()`, attempt servant creation while local population rules allow it.

On every kill:

`age += 100`

Therefore **kills accelerate both evolution and summon scheduling**.

At 20 TPS, a +100 kill bonus is roughly five seconds of natural age progression.

Technique: **combat success feeds an ecological age clock**.

## Evolution graph

### Gertrud line

`Anthony → Adelbert → Gertrud`

- Anthony advances after age >1800 (~90 seconds without kill acceleration).
- Adelbert advances after >2400 (~120 seconds).
- Gertrud is terminal in this chain and becomes a summoner.

Anthony additionally plants red flowers around itself whenever valid air/soil cells are found, making the familiar alter local scenery while alive.

### Charlotte line

`Pyotr → Charlotte`

- Pyotr advances after >3000 (~150 seconds).

Charlotte then has its own multi-form/revival phase system described in the boss catalog.

### Candeloro line

`Maid Puella Magi → Candeloro`

- Maid advances after >2000 (~100 seconds).
- Candeloro begins with age 120, so its servant-summon timeline starts partially advanced.

### Ophelia line

Court Lady begins as non-guide type.

`CourtLady(non-guide) → CourtLady(guide) → Ophelia`

- non-guide threshold: 1800;
- transition creates another CourtLady marked guide;
- guide threshold: 3000;
- then advances to Ophelia.

The same entity class therefore represents two ecological stages through synchronized `Type` state.

Technique: **same-class metamorphosis stage followed by class replacement**.

## Summoning ecology

The common population gate counts nearby `EntityMajo` inside a territory AABB, not only same-species servants.

Thus summoning pressure is capped by the **whole local witch/familiar ecosystem**, reducing runaway growth compared with per-species limits.

Default:
- summon check threshold: 200 age ticks;
- territory: 8 blocks horizontal / 4 vertical;
- reset count defaults to `canSummon()`.

### Gertrud
- local cap 6;
- servant is Adelbert 1/3 of the time, Anthony 2/3.

Because Anthony and Adelbert can themselves evolve back upward toward Gertrud, Gertrud creates a **self-renewing progression tree**, not disposable identical adds.

### Candeloro
- local cap 3;
- summons Maid Puella Magi;
- Maid can later advance back into Candeloro.

### Court Lady
- local cap 5;
- summons more Court Ladies;
- those can progress toward guide form and Ophelia.

### Homulilly Nutcracker
- local cap 64;
- territory 32 blocks;
- next summon age 100;
- reset after 8 successful summons, not 64.

Servant selection:
- Clara Dolls: 3%
- Liese: next 5%
- Lilia: next 20%
- Luiselotte: next 12%
- Lotte: remaining 60%

Each servant receives a reference to its parent Nutcracker.

This is a **large heterogeneous encounter population controller**, not a single summon spell.

## Parent-child kill feedback

`EntityHomulillyServant.onKillEntity`:
- forwards the kill to parent Nutcracker when present;
- then executes normal `EntityMajo.onKillEntity`, increasing the servant's own age too.

Therefore one servant kill can:
- accelerate that servant's own evolution;
- accelerate the parent encounter age/summon clock.

Technique: **hierarchical kill-credit feedback into encounter growth**.

ANCHOR should make this explicit through encounter events rather than raw entity references if persistence/unload matters.

## Homulilly servant evolution branches

### Lilia
- ranged Large Fireball attacker;
- evolves after 1500 into Luiselotte;
- adjusts vertical aim factor down sharply for targets >=10 blocks tall.

Technique: **target-size-aware projectile aim point**.

### Lotte
- melee;
- evolves after 1500 into Luiselotte.

On player hit, Lotte searches armor slots. If an equipped armor item's damage reduction is below the diamond equivalent, it replaces that stack with the diamond item of the same slot while attempting to preserve/clamp damage state.

Source behavior therefore appears to **upgrade weak player armor**, an unusual result for a hostile familiar. Treat this as a static behavior finding and potential design/logic anomaly until historical intent is found.

### Luiselotte
- stronger melee;
- evolves after 2000 into Clara Dolls;
- repeats the same weak-armor → diamond-armor replacement behavior.

### Liese
- 4 HP flying nuisance;
- custom free-flight target selection;
- special nearest-player target selector accepts only players who are **not on ground**;
- on player hit, tries up to 32 random main-inventory slots;
- if it finds a non-null stack whose item ID is not cobblestone, drops the entire stack and replaces that slot with one cobblestone;
- evolves after 3000 into Clara Dolls.

Technique: **inventory theft/replacement melee effect plus anti-air target specialization**.

This is a particularly strong source for “enemy attack changes player inventory state” research, but should be redesigned carefully for modern griefing/fairness.

### Clara Dolls
- 30 HP, 16 attack;
- fast 6-tick collision attack;
- on player hit selects an armor stack and inflicts durability loss scaled by remaining durability;
- can summon up to 3 Liese.

Technique: **durability-targeting enemy**, distinct from raw HP damage.

Together, Liese↔Clara creates a loop:
- Clara creates Liese;
- surviving Liese can mature into Clara.

## Shadow Puella Magi as copied combat archetypes

Prickle-spawned Shadow Puella Magi randomly selects one of seven character archetypes.

Type→weapon/attack vocabulary:
- 0 Madoka → Light Arrow short burst;
- 1 Homura → Garnet Bullet burst;
- 2 Sayaka → direct velocity melee;
- 3 Mami → staged Musket consume/deploy;
- 4 Kyouko → velocity melee + random knockback;
- 5 Kirika → Slowness then fast lunge/melee;
- 6 Yuri → Garnet Bullet burst + ambidextrous renderer presentation.

This is not a full copy of each hero's AI. It is a **compressed hostile imitation layer** that maps one type byte to:
- model/texture;
- held weapon;
- posture;
- attack routine.

Technique: **data-discriminated enemy archetype inside one entity class**.

### Maid Puella Magi

Maid extends Shadow but limits visual type to:

`rand.nextInt(2) * 4` → 0 or 4

Its attack override changes:
- type 0 → 7-shot-ish faster Light Arrow burst;
- type 4 → more aggressive velocity melee.

It then matures into Candeloro.

## Minor-familiar environment effects

### Anthony
Attempts around four quarter-offset local positions every living update; when air and red flower can stay, places a red flower block.

Technique: **ambient ecological world decoration performed by mob lifetime behavior**.

This should be budgeted/throttled in ANCHOR rather than attempted every tick.

## Design lessons

High-value independent primitives:

1. age-driven enemy metamorphosis;
2. kill-accelerated evolution;
3. same-class intermediate stage;
4. local ecosystem population cap;
5. heterogeneous summon pool;
6. servant kill feedback to parent encounter;
7. maturation loops among minions;
8. target-size-aware ranged aim;
9. anti-air-only target acquisition;
10. player inventory theft/replacement attack;
11. armor-durability attack;
12. hostile imitation archetype;
13. mob-driven ambient world decoration.

This system is conceptually closer to an **ecology/encounter growth graph** than to ordinary Minecraft summon AI.

## ANCHOR cautions

For Minecraft 1.20.1 Forge:
- persist ecological age only if design requires unload/reload continuity;
- use encounter IDs/UUIDs rather than raw parent entity references;
- enforce population budgets per encounter/chunk;
- avoid every-tick block placement;
- treat player inventory mutation as an explicit protected mechanic with server rules/config;
- separate “growth clock” from “summon budget” to avoid hard-to-reason feedback loops;
- instrument these systems in LAB because mass minion spawning plus pathfinding can dominate tick cost.
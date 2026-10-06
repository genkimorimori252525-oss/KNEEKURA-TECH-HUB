# QB-MOD 1.6.4.082 — Static performance / safety risk map

This is a source review, not a benchmark. No TPS/FPS/runtime PASS is claimed.

Purpose: identify code paths that should receive LAB instrumentation or bounded redesign during a 1.20.1 Forge reconstruction.

## Priority A — world mutation / explosive amplification

### Kriemhild terminal explosion
- explosion strength 80;
- block damage enabled.

Risk:
- extreme block ray/propagation work;
- huge permanent terrain loss;
- cascading drops/updates depending on environment.

ANCHOR:
- encounter-specific blast policy;
- cap affected blocks;
- optional visual-only/low-damage outer radius.

### Walpurgis terrain → TNT conversion
- connected terrain traversal;
- selected blocks replaced with primed TNT;
- many future explosion events are scheduled indirectly.

Risk:
- workload moves from one attack tick into many later TNT explosions;
- chain reactions and entity/block updates multiply cost.

ANCHOR:
- use bounded block-edit queue;
- per-encounter TNT/hazard budget;
- consider custom visual/explosion hazard instead of hundreds of vanilla TNT entities.

### Yuri terrain → TNT attack
Same primitive at smaller combat scale; should share the same bounded subsystem.

### Giant collision destruction
Homulilly Nutcracker and Charlotte second form:
- iterate body/collision region;
- remove blocks during living updates.

Risk:
- repeated chunk block writes every tick during movement;
- drop entity creation;
- neighbor updates.

ANCHOR:
- amortized terrain-damage queue;
- deduplicate positions across consecutive ticks;
- block tag protection;
- chunk-loaded bounds.

### Witch/GriefSeed forced spawn excavation
- expanding shell loops;
- collects block positions;
- destroys obstructions until giant spawn can fit.

Risk:
- synchronous burst when a transformation/incubation resolves.

ANCHOR:
- bounded multi-tick clearance job;
- explicit max volume/timeout/failure fallback.

## Priority A — entity-query pressure

### Kriemhild absorb pulse
Every 40 ticks:
- AABB roughly ±64 X/Z, ±32 Y;
- sorts/processes nearby living entities;
- stops around 101 processed targets.

Risk:
- large area plus entity count;
- cost rises in mob farms/modpacks.

LAB:
- 0/25/100/250 nearby living entities;
- measure query, sort and attack/heal cost.

### Garnet flying target acquisition
Custom flying target selection can query:
- target class;
- Ghast;
- Dragon;
- Wither;
- Nutcracker;
- optional broad class;
within ±32.

Then concatenates, sorts and filters.

`continueExecuting()` also calls `shouldExecute()`, potentially repeating acquisition while already engaged.

Risk:
- repeated large scans for many companions.

ANCHOR:
- split validate-current-target from acquire-new-target;
- acquisition cooldown;
- shared spatial/category query where many NPCs coexist.

### Large death cleanup
Walpurgis death scans a 200-block expanded AABB and kills every `EntityMob`.

Risk:
- huge entity query;
- unrelated mod mobs included.

ANCHOR:
- encounter membership set/tag;
- bounded cleanup over known members, not world-class scan.

## Priority B — spawn/summon amplification

### Nutcracker servant population
- local cap 64;
- heterogeneous servants;
- servants have pathfinding/combat/evolution;
- some branches create further minions.

Risk:
- encounter can become AI-heavy even before projectiles/TNT.

### Ecology loops
Examples:
- Gertrud → Anthony/Adelbert → Gertrud maturation;
- Candeloro → Maid → Candeloro;
- Clara → Liese → Clara.

Population gate limits local `EntityMajo` count, but:
- different encounter sources can overlap;
- kill-accelerated age shortens maturation;
- pathfinding load can dominate.

ANCHOR:
- encounter-global population budget;
- role-specific cap;
- spawn rate telemetry.

### Prickle → Shadow Puella
Projectiles embed and become delayed minion spawners.

Risk:
- projectile count can become later mob count;
- need lifecycle cleanup if parent encounter ends.

## Priority B — random teleport loops

Homura/Homulilly-family paths can attempt up to 64 random teleport destinations in one action.

Each attempt may perform:
- collision checks;
- liquid checks;
- path/position validity;
- particles/sound after success.

Risk:
- worst-case spikes in dense/invalid geometry.

ANCHOR:
- capped candidate sampler;
- reusable safe-position service;
- spread search across ticks when not latency-sensitive.

## Priority B — projectile bursts

Representative burst patterns:
- Madoka long: four arrows × repeated sequence;
- Madoka UF: repeated upward homing arrows every 5 ticks;
- Homura Rebellion: eight homing arrows every 15 ticks;
- Kyouko long: four Spears per burst;
- Spear2: one impact → six secondary Spears;
- Walpurgis multi-projectile attacks;
- Mami staged prop arrays.

Risks:
- entity count;
- collision/ray traces;
- homing target searches;
- renderer overhead.

Especially LightArrow2/3:
- homing projectiles independently search expanding AABBs if targetless.

ANCHOR:
- shared target assignment from shooter when possible;
- cap acquisition radius/projectile lifetime;
- pool visual-only bullets when physical entity semantics are unnecessary;
- LAB trajectory/entity-count profiling.

## Priority B — every-tick world decoration

Anthony attempts red-flower placement around itself in living updates.

Risk:
- block checks/writes from many familiars.

ANCHOR:
- random-tick/cooldown budget;
- do not perform environmental decoration every entity tick.

## Priority C — logging / accidental work

### Oktavia stdout
Wheel spawn candidate loop calls:
- `System.out.println(false)` on failures;
- `System.out.println(true)` on success.

Risk:
- console I/O can dwarf the tiny logical operation when combat repeats.

Remove in ANCHOR.

### Garnet tameable chat logging
`chatMessage` also `System.out.println`s owner messages when server-side.

Low frequency compared with Oktavia, but still legacy logging behavior.

Use structured debug logger gated by level.

## Safety / griefing risks

### Player capability mutation
Walpurgis and Nutcracker directly modify creative/flying flags on attackers.

Do not port.

### Inventory mutation
Liese:
- removes a random non-cobblestone main-inventory stack;
- drops it;
- replaces slot with one cobblestone.

Clara:
- damages armor durability.

Lotte/Luiselotte:
- replace sub-diamond armor with diamond armor.

These are interesting encounter mechanics but bypass normal loot/equipment expectations.

ANCHOR:
- config/rules;
- protect bound/undroppable items;
- server event hooks;
- clear telegraphing;
- avoid destructive inventory mutation by default.

### Direct health mutation
LightArrow3 and Homura Ultimate set target HP directly.

Risk:
- bypasses armor/damage hooks/invulnerability/mod compatibility.

ANCHOR:
- rule-aware custom DamageType / capped execute mechanic.

### Global weather/time mutation
Walpurgis repeatedly forces overworld storm/time.

Risk:
- affects unrelated players/dimensions/gameplay.

ANCHOR:
- encounter-local visual weather if possible;
- reversible server ambience controller;
- restore previous state.

## Persistence-related performance/logic risks

State loss can also create repeated work:
- special Grief Seed loses Homulilly flag on reload;
- Charlotte phase bit not persisted;
- EntityMajo age resets.

A load boundary may therefore repeat earlier incubation/evolution phases or switch behavior classes unexpectedly.

LAB should include save/reload probes, not only steady-state tick probes.

## Suggested LAB matrix

### Mob count
- 1 / 8 / 32 / 64 magical-girl/familiar entities.

### Projectile count
- 0 / 32 / 128 / 512 active projectiles;
- homing target present vs absent.

### Terrain
- open air;
- dense stone;
- mixed protected blocks;
- chunk border.

### Encounter
- Walpurgis normal vs low-health TNT phase;
- Nutcracker with servant population near cap;
- Kriemhild with 0/25/100+ nearby entities;
- Charlotte/Nutcracker moving through structures.

### Save boundary
- Homulilly ritual Grief Seed before/after reload;
- Charlotte second form before/after reload;
- familiar evolution age before/after reload;
- parent-linked servant before/after reload.

Metrics:
- server tick p50/p95/p99;
- entity tick time by class;
- block edits/tick;
- spawned entities/projectiles/TNT;
- allocations if profiler available;
- chunk loads caused;
- cleanup completion and leaked children.

## Summary

The legacy code contains many excellent spectacle mechanics, but the most reusable lesson is **budgeting**:

- entity count budget;
- query radius/frequency budget;
- projectile search budget;
- terrain edit budget;
- explosion budget;
- encounter lifetime/cleanup budget.

The ANCHOR implementation should preserve visual/combat intent while replacing synchronous “do everything now” loops with observable bounded systems.
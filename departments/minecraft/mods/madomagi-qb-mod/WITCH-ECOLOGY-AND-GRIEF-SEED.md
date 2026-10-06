# QB-MOD 1.6.4.082 — Witch ecology / Grief Seed lifecycle

Primary evidence: supplied QB-MOD archive SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`.

This subsystem is important because the MOD does not model witches only as isolated bosses. It implements a small ecology: age, kills, servant population, maturation, Grief Seed incubation and boss emergence interact.

## 1. EntityMajo common ecology

Locator: `MCP/puellamagi/mods/entity/monster/EntityMajo.java:29-55,83-152`.

Every witch-family entity has:
- an integer `age`;
- a successful-servant counter;
- an optional maturation threshold;
- an optional next-stage entity;
- an optional servant factory;
- a territory radius and local population cap.

Every living update:
1. age increments;
2. if `canAdvance() > 0` and age exceeds that threshold, `getAdvance()` is created at the same position;
3. if the replacement can spawn, an explosion-particle cue plays and the old entity dies;
4. independently, after `getNextSummonTime()`, a servant may be spawned;
5. servant admission counts all local `EntityMajo` in an expanded AABB, not just the same species;
6. after enough successful servant spawns, age is reduced by one summon interval and the local success counter resets.

A kill adds **+100 age**.

This gives a reusable loop:

`time + kills → maturity clock → evolution and/or servant production`.

The population check is not a globally unique minion quota. It is a **local witch-population density gate**.

### ANCHOR reconstruction note

Keep:
- kill-accelerated maturation;
- data-driven evolution graph;
- territory/population-limited spawning.

Rewrite:
- use explicit species/faction/population tags if the design needs per-family limits;
- do not scan a large AABB every tick; schedule/budget population checks;
- persist age/evolution state explicitly if continuity across chunk unload is required.

---

## 2. Confirmed evolution chains

### Gertrud line

- Anthony: `canAdvance() = 1800` → Adelbert.
- Adelbert: `canAdvance() = 2400` → Gertrud.

Anthony additionally plants red flowers near itself when suitable, making the servant's non-combat behavior part of the ecology.

### Charlotte line

- Pyotr: `canAdvance() = 3000` → Charlotte.
- Charlotte is created with a random revival/phase count of 1–3.

This means a low-tier servant can mature directly into a multi-stage boss.

### Candeloro line

- Maid Puella Magi: `canAdvance() = 2000` → Candeloro.
- Maid Puella Magi randomly selects only two visual/weapon archetype values through `rand.nextInt(2) * 4`.

### Ophelia line

Court Lady:
- non-guide threshold 1800 → a Court Lady configured as guide;
- guide threshold 3000 → Ophelia;
- can also summon up to 5 Court Ladies locally.

Ophelia itself can maintain a Court Lady servant and a separate phantom pool.

### Homulilly / Nutcracker servant lines

Confirmed paths:
- Lilia: 1500 → Luiselotte.
- Lotte: 1500 → Luiselotte.
- Luiselotte: 2000 → Clara Dolls.
- Liese: 3000 → Clara Dolls.
- Clara Dolls can summon Liese.

Each replacement preserves its Homulilly/Nutcracker parent reference where the source implements it.

Homulilly Nutcracker:
- starts with age 1200;
- local witch cap 64;
- successful-summon batch size 8;
- base summon interval 100 ticks;
- territory radius 32;
- weighted servant factory:
  - 0–2: Clara Dolls;
  - 3–7: Liese;
  - 8–27: Lilia;
  - 28–39: Luiselotte;
  - 40–99: Lotte.

Nutcracker's own kills call the common `EntityMajo.onKillEntity` and additionally heal it by 3, so kills both **accelerate ecology and sustain the boss**.

---

## 3. Servants with inventory / equipment attacks

These are not generic melee mobs.

### Liese — item displacement / replacement

On player melee:
- tries up to 32 random main-inventory slots;
- if a non-null, non-cobblestone stack is found, drops that stack into the world;
- replaces the slot with one cobblestone;
- then continues normal melee.

Technique: **combat hit mutates player inventory and externalizes the displaced item**.

Do not port literally without explicit game-design consent and server-side inventory transaction safety.

### Lotte / Luiselotte — armor transformation

On player melee:
- scans armor slots;
- if an equipped armor item has lower damage reduction than the diamond equivalent;
- replaces it with the matching diamond armor piece;
- attempts to carry an adjusted damage/durability value forward.

This is a surprising *beneficial-looking* side effect attached to an enemy hit. It may be deliberate theme behavior or a historical implementation oddity; it is not labeled a bug without stronger evidence.

Technique: **equipment-class transformation on hit**.

### Clara Dolls — targeted armor wear

Clara Dolls selects an equipped armor stack and applies durability damage according to its remaining durability:
- >500 remaining → about 10% of the remaining value;
- >100 → 50;
- >25 → 8;
- otherwise 3.

Technique: **enemy pressure routed through equipment durability rather than only HP**.

---

## 4. Grief Seed: item → entity → boss incubation

### Item form

Locator: `item/ItemGrifSeed.java:16-90`.

Properties:
- stack size 1;
- max damage 63;
- glints while damage < max.

Using it on a block creates an `EntityGriefSeed`, transfers item damage into the entity's Soul Gem damage and consumes the item unless creative.

This makes item durability a persisted **corruption/incubation parameter** rather than merely weapon wear.

### Special glass/water ritual

A dropped Grief Seed performs an environmental check:
- finds still water beneath/around its sample point;
- requires every non-center cell of the surrounding 3×3×3 cube to be glass;
- if valid, creates an EntityGriefSeed in the center;
- initializes a countdown;
- calls `setHomulilly()`;
- consumes the dropped item.

This is a hidden **world-structure ritual → species override** and specifically points the incubation toward Homulilly Nutcracker.

Technique: **item entity + multiblock environment predicate → alternate boss lifecycle**.

---

## 5. EntityGriefSeed incubation

Locator: `entity/monster/EntityGriefSeed.java:138-191,193-312,542-661`.

EntityGriefSeed behaves partly like an embedded projectile and partly like a persistent creature.

It does not despawn normally.

### Player-proximity activation

Countdown logic runs only when a player is within 16 blocks:
- -1 → initialize;
- >0 → decrement;
- <=0 → spawn a witch.

Client warning particles intensify below countdown thresholds 1000, 500 and 100.

Technique: **proximity-activated dormant world hazard with escalating visual telegraph**.

### Corruption controls incubation speed

`setNewCountDown()`:

`500 + random(0..999) - SoulGemDamage * 5`

Higher transferred damage therefore shortens the incubation window.

Technique: **item state from a previous gameplay loop changes future world-event latency**.

### Normal species selection

`rand.nextInt(5)` selects:
- Gertrud;
- Charlotte;
- Oktavia;
- Candeloro;
- Homulilly.

There is a default switch branch returning Walpurgisnacht, but `nextInt(5)` can only produce 0–4. The Walpurgis default is therefore unreachable under this selector.

This is a source-level dead-branch/anomaly candidate, not a historical bug claim.

### Special ritual species

If `isHomulilly` is set, the selector bypasses the normal random table and produces Homulilly Nutcracker.

### Spawn-space preparation

The entity first tries 16 nearby positions.

If no valid position is found, `forcedSpawnMajo`:
- grows a shell around the seed;
- accumulates shell cells;
- deletes obstructing blocks;
- protects bedrock, Mami Ribbon and Kyouko Shield;
- low-value terrain has only a 0.1% drop chance, other removed blocks 10%;
- retries until the target witch can spawn or the shell exceeds the target-height condition.

This is the same broad design family as magical-girl → giant-witch conversion: **narrative state transition prepares world topology for the new entity**.

ANCHOR must use bounded block-edit jobs and permission/protection checks.

---

## 6. Natural Grief Seed population

`EntityGriefSeed.getCanSpawnHere()`:
- uses configurable `GSSpawning` probability;
- requires non-Peaceful;
- requires configured low-light condition;
- requires no collision;
- rejects liquids.

So a Grief Seed is not merely player-produced. It is itself a naturally spawnable world entity/hazard.

On Peaceful, existing seed entities are removed server-side.

---

## 7. Soul Gem as witch proximity sensor

Locator: `item/ItemSoulGem.java:41-150`.

The Soul Gem item:
- max damage 63;
- uses two render passes;
- darkens the gem layer as item damage crosses 16 / 32 / 48;
- while selected, searches within 15 blocks for EntityGriefSeed or any EntityMajo;
- if found, stores `nearGriefSeed=true` in item NBT;
- glints and changes rarity from common to rare.

Technique: **held item performs local threat sensing and expresses it through presentation rather than a HUD-only marker**.

This completes a circular system:

`magical-girl corruption → Grief Seed cleansing/resource state → Grief Seed world incubation → witch ecosystem → nearby Soul Gem warning`.

That loop is more valuable than any single mob implementation.

---

## 8. Ecology-technique inventory

Preserve independently:

1. kill-accelerated maturation clock;
2. entity replacement as biological evolution;
3. local population-density servant gate;
4. multi-stage servant→boss evolution graph;
5. parent-reference inheritance across evolution;
6. enemy attack that mutates inventory/equipment;
7. persistent thrown/embedded seed entity;
8. player-proximity activated incubation;
9. resource durability/state controlling hatch latency;
10. environmental multiblock ritual overriding hatch species;
11. random spawn attempt followed by topology preparation;
12. held-item proximity threat sensor;
13. state-dependent visual warning escalation.

Do not flatten these into one “witch system” template.
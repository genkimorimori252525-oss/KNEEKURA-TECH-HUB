# Five Difficulties X1 Preservation Port — P6 runtime scenario checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p6-2026-10-07`

Parent:
P5 dedicated-server runtime smoke branch.

Status: **P6 COMPLETE — Homing projectile + Sakuya FULL/HALF world behavior pass in a real Forge 1.20.1 dedicated server**

## Scope

P6 moves beyond “the server boots” and mutates an actual Minecraft world.

A bounded server-side scenario harness creates test entities in the loaded world and validates:

- Sakuya FULL_STOP freezes an eligible target entity;
- Sakuya HALF_SPEED advances that target at approximately half tick rate;
- the red Homing Amulet projectile exists, moves under its live 1.20.1 code path and damages a target;
- the P5 startup/registry/Mixin smoke still passes.

The harness fails fast when an assertion fails and stops the dedicated server after success.

## Latest hardened validation

GitHub Actions run:

- **37535774768**
- head `f4a570b014ca7dcad1e324c7cc535c3e5274c150`
- conclusion: **SUCCESS**

Pipeline:
- pure Java regressions: PASS;
- resource JSON validation: PASS;
- exact official Forge 1.20.1-47.4.6 MDK preparation/SHA validation: PASS;
- Mixin-enabled `compileJava jar`: PASS;
- real dedicated-server startup: PASS;
- bounded world runtime scenario: PASS;
- artifact retention: PASS.

Dedicated server reached:

`Done (2.653s)! For help, type "help"`

## Runtime receipts

Scenario start:

`FIVE_DIFFICULTIES_P6_SCENARIO_START sourceId=1 targetId=2 pos=0.5,-58.0,0.5`

### FULL_STOP

Marker:

`FIVE_DIFFICULTIES_P6_FULL_PASS baselineTick=4 observedTick=4 pos=(0.5, -58.0, 4.5)`

Meaning:
- the target's baseline entity tick count was 4;
- after the full-stop observation window it remained 4;
- the entity remained at the recorded frozen position.

This is the first real-Minecraft confirmation that the P3 tick interception actually suppresses ordinary target simulation.

### HALF_SPEED

Marker:

`FIVE_DIFFICULTIES_P6_HALF_PASS baselineTick=6 observedTick=9 delta=3`

The bounded observation window advanced the target by 3 ticks rather than the full-rate amount, confirming the deterministic alternate-tick HALF_SPEED machinery is active in the real server.

This validates the **modernized half-rate scheduler**, not the exact 1.7.10 internal post-tick field mutation.

### Red Homing Amulet

Hardened marker:

`FIVE_DIFFICULTIES_P6_HOMING_PASS ticks=11 startHealth=20.0 endHealth=15.0 targetPos=(0.5, -58.0, 8.5)`

Observed:
- live Homing projectile traversed the world;
- target was acquired/hit;
- the canonical normal red damage of 5 was applied;
- target health changed 20 → 15;
- projectile/source attribution and spawn hardening did not break runtime behavior.

Scenario summary:

`FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO_PASS fullFrozenTicks=4 halfObservedDelta=3 homingTicks=11 homingHealthDelta=5.0`

Final CI verdict:

`P6_WORLD_RUNTIME_PASS`

## What P6 proves

P6 upgrades these surfaces from compile-only to **real dedicated-server runtime evidence**:

- Five Difficulties mod/Mixins load in Forge 1.20.1;
- P3 time controller changes actual entity simulation;
- FULL_STOP freezes an eligible world entity;
- HALF_SPEED changes actual tick cadence;
- the red Homing projectile moves and damages a target;
- the current vertical slice survives server startup/world ticking together.

## What P6 does not prove

Still unverified:

- client renderer appearance with private X1 PNG overlay;
- item hand/inventory appearance;
- expanding Sakuya dark-field visual parity;
- client interpolation during frozen time;
- actual player right-click/charge interaction;
- actual two-player network behavior;
- frozen player/vehicle behavior with a connected client;
- Watch consume/return inventory lifecycle through a real player;
- StopWatch through a real player;
- Sakuya knife placement/release;
- Murdering Doll same-owner time-stop exception;
- arbitrary third-party modded entities;
- full spell-card catalog;
- Master Spark / lasers.

## P7 recommendation

The next preservation gate should be **client-integrated runtime**, not more server-only content.

P7 priorities:

1. start a real Forge 1.20.1 client with the SHA-verified private X1 texture overlay;
2. verify item models and controller renderer load without missing-texture/model errors;
3. capture fixed-camera screenshots of:
   - red Homing Amulet;
   - Sakuya Watch controller;
   - StopWatch controller;
   - expanding dark field;
4. verify client simulation visibly freezes while the source remains active;
5. only after that, add a connected-client interaction scenario for Watch charge/toggle/use.

Do not expand to all spell cards before the current visual/time-stop vertical slice has client evidence.

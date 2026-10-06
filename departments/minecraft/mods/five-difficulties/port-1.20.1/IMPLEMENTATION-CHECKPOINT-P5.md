# Five Difficulties X1 Preservation Port — P5 runtime checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p5-2026-10-07`

Parent:
`jolly/five-difficulties-1201-port-p4-2026-10-07`

Status: **P5 COMPLETE — current Homing + Sakuya vertical slice starts successfully in a real Forge 1.20.1 dedicated-server process**

## Scope

P5 raises the evidence level from compile/package validation to a bounded Minecraft runtime startup check.

The runtime target is still:
- Minecraft 1.20.1;
- Forge 47.4.6;
- Java 17;
- the P4 red Homing Amulet + Sakuya Watch/StopWatch + time-domain Mixins.

P5 does not claim client visual parity or full interaction parity.

## Dedicated-server runtime harness

CI:
`.github/workflows/five-difficulties-port-p0.yml`

The P5 workflow:

1. runs all pure Java preservation regressions;
2. validates JA/EN resource JSON;
3. downloads the exact official Forge 1.20.1-47.4.6 MDK;
4. verifies MDK SHA-1
   `1a1c045f235262ff617e285ea2156571ea93bfbe`;
5. overlays the committed port source;
6. patches validation Gradle config for the P3/P4 Mixins;
7. runs `compileJava jar`;
8. verifies Mixin manifest/config/refmap packaging;
9. creates a temporary EULA-accepted offline flat-world server;
10. runs `runServer --args='nogui'`;
11. requires a runtime self-check marker and Minecraft `Done (...)` marker;
12. rejects startup/crash-report failure markers;
13. stops the smoke server through a dedicated inherited environment flag;
14. retains bounded logs/evidence as an Actions artifact.

## Runtime self-check

`RuntimeSmokeChecks` subscribes to `ServerStartedEvent`.

It verifies at runtime:

### Registered item instances
- Homing Amulet → `HomingAmuletItem`;
- Sakuya Watch → `SakuyaWatchItem`;
- StopWatch → `SakuyaStopWatchItem`.

### Registered EntityType factories
The smoke creates non-world-added test instances through each EntityType factory and verifies:
- Homing projectile → `HomingAmuletProjectile`;
- Sakuya controller → `SakuyaTimeControllerEntity`.

### Registry keys
Verified namespace/path:
- `five_difficulties_port:homing_amulet`;
- `five_difficulties_port:sakuya_watch`;
- `five_difficulties_port:sakuya_stopwatch`;
- `five_difficulties_port:homing_amulet_projectile`;
- `five_difficulties_port:sakuya_time_controller`.

### X1 time-policy core
Representative runtime assertions verify:
- mature LivingEntity → FREEZE in FULL_STOP;
- age-1/new entity → ALLOW through X1 two-tick grace;
- source entity → ALLOW;
- mature LivingEntity → HALF_SPEED in HALF mode.

This test intentionally does not mutate a real world entity yet.

## Final successful runtime evidence

GitHub Actions run:
- **37533730730**
- head:
  `dac041fab79744f18fddd54e6d37db8c286920c1`
- conclusion: **SUCCESS**

Server log evidence:
- `Done (1.927s)! For help, type "help"`
- `FIVE_DIFFICULTIES_P5_RUNTIME_SMOKE_PASS serverVersion=1.20.1 dedicated=true`
- `P5_DEDICATED_SERVER_RUNTIME_PASS`

The final run also passed:
- pure Java regressions;
- resource JSON validation;
- exact MDK verification;
- Forge compile/package;
- Mixin packaging checks;
- bounded artifact upload.

## Failure / repair history

### Failure 1 — invalid EntityType smoke assumption

Initial runtime run reached a real Minecraft world startup successfully, but the smoke failed on:

`homing projectile EntityType base class`

Cause:
Forge/Minecraft 1.20.1 `EntityType#getBaseClass()` returns `Entity.class` rather than preserving the builder's concrete generic class.

Repair:
- remove concrete-class equality through `getBaseClass()`;
- instantiate via the EntityType factory in the actual ServerLevel;
- assert `instanceof HomingAmuletProjectile` / `SakuyaTimeControllerEntity`.

This was a **test-harness defect**, not a registry/factory defect.

### Failure 2 — malformed language JSON

The first server log warned that `en_us.json` contained a literal trailing `\\n` after the JSON object.

Repair:
- rewrite JA/EN files as normal JSON with an actual terminal newline;
- add `python -m json.tool` validation before MDK compilation.

This did not prevent the server world from starting, but it was fixed before P5 completion.

### Harness improvement — deterministic auto-stop

The first auto-stop attempt relied on a Gradle JVM `-D` property, which is not guaranteed to propagate into the Minecraft JavaExec process.

Repair:
- use inherited environment variable
  `FIVE_DIFFICULTIES_RUNTIME_SMOKE_EXIT=1`;
- after emitting the PASS marker, `RuntimeSmokeChecks` calls
  `MinecraftServer.halt(false)`.

This keeps normal gameplay unaffected because the environment flag exists only in the bounded CI smoke.

## What P5 proves

Evidence-backed now:
- mod classloading succeeds in a real Forge dedicated server;
- required registries resolve after Forge startup;
- EntityType factories construct their expected modern classes;
- Sakuya policy classes are operational under the transformed runtime;
- Mixins coexist with server startup;
- a world reaches the Minecraft `Done` state;
- runtime self-check runs from Forge's server event bus.

## What P5 does NOT yet prove

Still unverified:

### Actual world interaction
- Homing Amulet right-click spawning five/two live projectiles in-world;
- homing acquisition and collision against a real target;
- Watch charge/release through real player input;
- actual FULL/HALF freezing of a spawned mob/projectile;
- Watch return-to-inventory after expiry;
- StopWatch expiry in-world.

### Client
- client startup with private X1 PNG overlay;
- item icons;
- red Homing renderer appearance;
- Watch clock model;
- expanding dark sphere;
- visual interpolation while another entity is frozen.

### Multiplayer
- source player vs second player;
- movement-packet rejection;
- vehicle/passenger synchronization;
- overlapping controllers from two players.

### Cross-mod compatibility
- arbitrary modded LivingEntity;
- modded projectile/entity tick assumptions;
- external Mixins touching the same server/client methods.

## Next gate — P6 world-mutating GameTest / runtime oracle

P6 should stay narrow and prove the existing features before porting more content.

Recommended order:

1. add Forge GameTests or an equivalent server-side test harness;
2. spawn a real target LivingEntity and a Homing projectile;
3. assert X1 two-tick grace / FULL_STOP tick freeze;
4. assert HALF mode advances approximately every second logical tick;
5. assert controller bounded expiry;
6. assert consumed Watch return lifecycle using a fake/server player where the harness safely supports it;
7. test Homing projectile movement/hit against a real mob;
8. retain server-side traces:
   - tick count;
   - position;
   - delta movement;
   - controller mode;
   - entity age;
   - health.

Client rendering parity should remain a separate P7-style gate if headless automation cannot prove it.

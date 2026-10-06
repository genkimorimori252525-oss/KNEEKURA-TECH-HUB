# Five Difficulties X1 Preservation Port — P3 implementation checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p3-2026-10-07`

Parent:
`jolly/five-difficulties-1201-port-p2-2026-10-07`

Status: **P3 COMPLETE — canonical X1 Sakuya entity-time policy is represented by compiled 1.20.1 Mixins**

## Canonical X1 source basis

P3 directly re-read the reacquired canonical X1 archive:

`SHA-256 6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`

Primary source files:
- `EntitySakuyaWatch.java`
- `EntitySakuyaStopWatch.java`
- `ItemSakuyaWatch.java`
- `ItemSakuyaStopWatch.java`
- `THKaguyaTimeStopEventHandler.java`
- `THSC_SatuzinDoll.java`

See `P3-SAKUYA-TIMESTOP-EXACT.md`.

## Exact X1 rules frozen in P3

### Scope

The X1 Watch operates on **Entity only**.

It does not actively stop:
- block scheduled ticks;
- fluid scheduled ticks;
- BlockEntities;
- chunk/random ticks;
- particles;
- animated textures;
- world day time.

Those broader Roundabout behaviors are deliberately absent.

### Field

The controller follows its source at:
- distance 1.2;
- yaw offset -30°;
- pitch-following;
- eye-height -0.5 vertical placement.

Entity query shape is a **40-block AABB expansion**, not a sphere.

Duplicate activation precheck is a 20-block AABB.

### Exclusions

Not frozen/slowed:
- source user;
- entity carrying/ridden by source user in the legacy relation;
- ItemFrame;
- Painting;
- entities younger than 2 ticks;
- same-owner time-stop-movable spell-card objects.

### Exact mode contracts

- TIME_STOP = 0
- TIME_STOP_IN_SPELLCARD = 1
- TIME_HALF = 2
- TIME_STOP_WITH_LIMIT = 5
- TIME_HALF_WITH_LIMIT = 6

Dormant modes 3/4 exist in source but have no canonical creation call-site.

### Processing windows

Static X1 control-flow is represented as processing-update counts:
- spell-card stop: 61 max processing updates;
- limited full stop: 101;
- limited half speed: 161;
- StopWatch: 40.

Persistent creative full/half modes have no fixed duration.

### End conditions

Controller stops on:
- missing/dead source;
- source hurt;
- Watch-family source sneak after grace;
- no player remaining in the 40-block field;
- duplicate-controller conflict;
- bounded duration expiry.

## Modern 1.20.1 machinery

### Synced controller entity

`SakuyaTimeControllerEntity` stores:
- source entity id;
- FULL_STOP / HALF_SPEED mode;
- controller kind;
- start tick;
- duration.

It follows the canonical X1 watch-center geometry and is indexed per Level by `SakuyaTimeStopRuntime`.

The controller starts affecting the world on the **next logical world tick**, matching the fact that the X1 controller first processes after spawning.

### Entity tick interception

`ServerLevelTimeMixin`:
- cancels eligible non-passenger entity ticks;
- cancels eligible passenger ticks.

`ClientLevelTimeMixin`:
- mirrors cancellation client-side to reduce simulation/interpolation drift.

### ServerPlayer handling

Modern ServerPlayer simulation is partly driven through the network connection path.

`ServerGamePacketListenerTimeMixin` therefore:
- gates `ServerPlayer.doTick()`;
- rejects movement packets for frozen players;
- rejects frozen player input;
- rejects frozen vehicle movement and re-syncs vehicle position.

The time-source player remains exempt.

### Half speed

X1's original half-speed was a post-tick motion/timer correction.

P3 modernizes that to deterministic **alternate tick cancellation** while retaining:
- X1 1/2 intended rate;
- controller phase determinism;
- source/exclusion/field policy.

This is an implementation modernization, not a claim of identical 1.7.10 internal field mutation.

### New-entity behavior

X1 freezes ordinary entities only once their age reaches two ticks.

P3 uses this explicit two-tick grace instead of Roundabout's gradual projectile deceleration.

## Same-owner spell exception

`X1TimeStopMovable` is the modern hook for X1's spell-card exception.

An entity may:
- declare it can move in the source user's X1 time stop;
- receive an explicit time-field callback.

This is intended for Murdering Doll's later `specialProcessInTimeStop()` parity.

No generic JoJo projectile/Stand exemption is included.

## Mixin packaging

Resource:
`five_difficulties_port.mixins.json`

Mixins:
- ServerLevelTimeMixin
- ServerGamePacketListenerTimeMixin
- ClientLevelTimeMixin

CI patches the exact Forge MDK Gradle build only for validation and verifies:
- manifest `MixinConfigs: five_difficulties_port.mixins.json`;
- mixin config present in jar;
- refmap present in jar.

## Verification

Latest P3 GitHub Actions validation:

- run **37527522708**
- head `2f6f802ca344aef232f871c8eac75ff8844f9bc8`
- conclusion: **SUCCESS**

Verified:
- pure Java preservation regressions: PASS;
- X1 Sakuya policy/geometry regressions: PASS;
- official Forge 1.20.1-47.4.6 MDK SHA verification: PASS;
- Mixin-enabled `compileJava jar`: PASS;
- Mixin manifest/config/refmap packaging checks: PASS;
- bounded evidence artifact upload: PASS.

## Deliberately incomplete

P3 does **not** yet claim Minecraft runtime parity.

Not yet implemented/verified:
- player-usable Sakuya Watch Forge item;
- player-usable StopWatch Forge item;
- controller model/texture/clock visual;
- item-return lifecycle for non-creative Watch;
- old Watch item metadata/glint UX;
- actual Murdering Doll spell-card implementation;
- X1 exact client interpolation visual comparison;
- live multiplayer two-player test;
- TNT/falling-block/minecart/boat behavior under actual runtime;
- full-stop interaction with arbitrary third-party modded entities.

## Next gate — P4 usable Sakuya items + runtime oracle

P4 should make the system player-accessible before expanding more Five Difficulties content:

1. implement Sakuya Watch item with metadata-equivalent FULL/HALF mode state;
2. preserve 20/48 tick charge semantics and creative immediate activation;
3. implement limited Watch item consume/return lifecycle;
4. implement disposable StopWatch;
5. add original private texture-overlay import for both item/controller visuals;
6. run a bounded Minecraft 1.20.1 client/server smoke test;
7. compare frozen mob/projectile/player behavior against X1 observations.

Do not begin all spell cards or mass bullet conversion before this gate.

# Youkai's Homecoming — Danmaku architecture research — 2026-10-05

## 1. Research question

How does Youkai's Homecoming implement dense Touhou-style projectile patterns inside Minecraft
without reducing the system to ordinary vanilla projectile entities?

Pinned source:
`Minecraft-LightLand/Youkai-Homecoming@6d5744269aa597370a265d5c20eeb69902629441`

Evidence labels:

- **DIRECT_OBSERVATION** — visible in pinned source or exact diff.
- **AUTHOR_CLAIM** — release/project/tutorial material.
- **INFERENCE** — engineering lesson derived from evidence.
- **UNKNOWN** — not established.

## 2. Architecture overview

The danmaku system has two major code domains.

### fastprojectileapi

A generic projectile substrate embedded in the repository:

- simplified entity lifecycle
- projectile/laser collision
- entity-section caches
- virtual client projectile storage
- render batching
- spell-circle rendering

### Youkai Homecoming danmaku/spell layer

Game semantics:

- colored bullet/laser item types
- damage rules
- grazing
- spell-card battles
- pattern movers
- boss/player spell patterns
- custom spell editor/data
- battle resources and erasure

This separation is one of the most useful design choices in the target.

## 3. Simplified Entity contract

`SimplifiedEntity` still extends Minecraft `Entity`, retaining useful identity/network/position
contracts, but removes large amounts of generic behavior.

DIRECT_OBSERVATION:

- `tick()` only calls its simplified `baseTick()`;
- no fluid pushing;
- no splash effect;
- no sprint particles;
- no inside-block checks;
- fire state is disabled;
- explosion interaction is ignored;
- piston reaction is IGNORE;
- capability requests return empty;
- entity type registry ID is cached.

Locator:
- `fastprojectileapi/entity/SimplifiedEntity.java#L24-L104`

**Technique:** retain the host engine's identity/serialization shape while deliberately opting out
of irrelevant generic lifecycle work.

## 4. Projectile lifecycle is explicit

`BaseProjectile.tick()` performs:

1. collision query along the current movement vector;
2. hit handling;
3. lifetime test;
4. movement update;
5. chunk/ticking-region validity cleanup.

Movement is direct:

```text
ProjectileMovement = updateVelocity(previous velocity, position)
set velocity
update visual rotation
setPos(position + velocity)
```

Locator:
- `fastprojectileapi/entity/BaseProjectile.java#L34-L92`

This makes trajectory control much easier than inheriting many vanilla projectile assumptions.

## 5. Virtual NPC danmaku: Entity-shaped objects outside the normal entity manager

This is the strongest system-level finding.

`YoukaiEntity` stores:

- `LinkedList<SimplifiedProjectile> allDanmakus`
- temporary spawn list while iterating
- `toBeSent` spawn-sync batch

When a spell calls `shoot` with a SimplifiedProjectile:

- it is appended to the owner's danmaku collection;
- it is **not necessarily added to the Level entity manager**;
- it is recorded for client synchronization.

Then `tickDanmaku()` manually:

- snapshots old position/rotation;
- increments projectile tick;
- runs projectile tick;
- removes invalid bullets;
- merges bullets created while iterating;
- sends the accumulated new-bullet batch to tracking clients.

Locators:
- `YoukaiEntity.java#L548-L603`

**Technique:** for owner-scoped ephemeral swarms, the expensive host-engine entity container can be
replaced by a domain-specific owner collection while keeping Entity-like object semantics.

This is not merely rendering optimization. It changes **simulation ownership**.

## 6. Safe spawn-during-iteration pattern

A spell can expire one projectile and spawn several new ones during the same danmaku tick.

Directly appending into `allDanmakus` while iterating would invalidate iteration/order.

The code uses:

```text
active list
  |
tick each bullet
  |
new bullets -> temp
  |
end pass
  |
active.addAll(temp)
```

**Technique:** projectile pattern engines need an explicit spawn staging phase. This also creates a
clear same-tick/next-pass semantic boundary.

## 7. Client virtualization

`DanmakuToClientPacket` carries a batch of projectile descriptors:

- entity type registry ID
- synthetic/projectile entity ID
- position
- pitch/yaw
- velocity
- concatenated custom spawn bytes

Client reconstructs each projectile through its EntityType, reads spawn data, then adds it to
`ClientDanmakuCache`.

The cache owns:

- linked list for tick/render iteration
- int-ID map for erase lookup

It is ticked by `ProjectileRenderHelper` on client LevelTick END.

It is rendered at `RenderLevelStageEvent.Stage.AFTER_ENTITIES`.

The reconstructed projectiles are **not normal Level-managed entities**.

Locators:

- `fastprojectileapi/render/virtual/DanmakuToClientPacket.java`
- `fastprojectileapi/render/virtual/DanmakuClientHandler.java`
- `fastprojectileapi/render/virtual/ClientDanmakuCache.java#L62-L171`
- `fastprojectileapi/render/core/ProjectileRenderHelper.java#L37-L59`

## 8. Spawn synchronization is batch-oriented

Early virtual implementation sent one projectile packet at a time.

Release 2.3.15 changes `DanmakuManager.send` to accept a list and changes
`DanmakuToClientPacket` to encode multiple projectile descriptors with one concatenated custom
spawn-data stream.

DIRECT_OBSERVATION:
- commit `aa20f6e6d27e7765541a3b6e60ac352369714b06`

AUTHOR_CLAIM:
- 2.3.15 changelog: "Optimize danmaku rendering"

**Technique:** bullet hell does not only need render batching; **spawn network batching** also matters.

## 9. Client render queue groups bullets by visual type

Individual projectile renderers create compact render records rather than writing final vertices
immediately.

`ProjTypeHolder` interns each `RenderableProjectileType` and gives it a stable index.

`ProjectileRenderHelper.RenderQueue` stores one list per type.

During flush:

```text
all visible bullets
    ↓
type-specific Ins records
    ↓
array of lists indexed by ProjTypeHolder
    ↓
one type.start(buffer, list) per visual type
    ↓
bulk vertex emission
```

Locators:

- `fastprojectileapi/render/core/ProjTypeHolder.java`
- `fastprojectileapi/render/core/ProjectileRenderHelper.java#L62-L84`
- `fastprojectileapi/render/type/SimpleProjectileType.java`
- laser render types

**Technique:** separate per-object transform preparation from render-state/buffer submission.

## 10. RenderType objects are memoized

`DanmakuRenderStates` memoizes projectile/laser RenderTypes by:

- texture
- display mode (transparent/additive/etc.)

This avoids constructing equivalent render-state objects repeatedly.

It also normalizes ordinary danmaku SOLID requests to the transparent path.

## 11. Direct buffer fast path with explicit compatibility fallback

`BulkDataWriter` checks whether its VertexConsumer is a direct `BufferBuilder`.

When safe, it writes:

- xyz floats
- uv floats
- packed RGBA bytes

directly into the BufferBuilder's backing structure and advances internal offsets/counts through an
accessor.

When:

- the consumer is not a BufferBuilder, **or**
- ImmediatelyFast is loaded,

it uses ordinary public `VertexConsumer.vertex(...).uv(...).color(...).endVertex()`.

Locator:
- `fastprojectileapi/render/core/BulkDataWriter.java`

This fallback was added by commit:
`2bb02d3433b558c5bc63ac201865ca8550caec4e`
("fix danmaku rendering crash with ImmediatelyFast").

**Technique:** keep an unsafe implementation-level optimization behind a compatibility gate and a
semantically equivalent public-API path.

Do not treat the direct write itself as universally reusable.

## 12. Entity-section collision cache

Dense bullets create a different problem on the server: repeatedly asking the Level for nearby
entities.

`EntityStorageCache` is:

- scoped to one ServerLevel + gameTime;
- lazily filled by section;
- backed by a fast section map.

`SectionCache` directly reads the persistent entity section storage once for that section and
stores pickable entities.

A query then scans only relevant section cells.

Locators:

- `collision/EntityStorageCache.java`
- `collision/SectionCache.java`
- `collision/IEntityCache.java`

**Technique:** cache spatial candidate sets for one simulation tick, not collision outcomes.

That keeps correctness tied to the current tick while amortizing repeated broadphase discovery.

## 13. Shooter-local matrix cache

Entities implementing `EntityCachingUser`, including Youkai actors, provide a `UserCacheHolder`.

Each tick, the holder creates an **11 x 11 x 11 section pointer matrix** centered on the shooter
(`R=5`), lazily referencing the global tick cache.

Bullets from the same shooter reuse it.

Locator:
- `collision/UserCacheHolder.java`
- `collision/UserMatrixCache.java`

Commit:
`f1da61322d564afa5629bfb79b1b736636cd4aef`
("user section cache")

**Technique:** exploit the fact that a bullet swarm has a common emitter/locality. Per-owner cache
locality can be stronger than a completely global cache.

## 14. Moving-target broadphase

Candidate target AABB is expanded by its current velocity before broadphase intersection.

This means a fast entity whose current box is outside the projectile search box can still enter the
candidate set if its movement during the tick crosses it.

Commit `4faaa691208247718cc203a20aff23efcb7fbf20`.

## 15. Moving-target narrowphase

`ProjectileHitHelper.checkHit` does not test only the target's current AABB.

It samples predicted boxes along target velocity.

Current rule:

```text
speed = |targetVelocity|
samples = min(8, floor(speed / 0.5))

for i = 0..samples:
    box = currentAABB moved by velocity * i/samples
    test projectile segment against box
```

This history evolved from:

- max 4 samples / 0.8 threshold in `4cb84d2`
- max 8 / 0.5 threshold plus shared laser helper in `4faaa69`

Release notes explicitly describe improved collision against high-speed entities.

**Technique:** collision must account for **target motion**, not only projectile motion, when both
objects may move substantially per tick.

## 16. Graze reuses the same collision system

`IYHDanmaku.GRAZE_RANGE = 1.5`.

Direct hit and graze are not two unrelated scans.

For a normal bullet:

1. get broadphase candidates using radius + graze;
2. try direct hit with direct radius/hitbox;
3. only when direct hit fails, test expanded graze radius;
4. invoke graze behavior for players.

For lasers, the direct and graze tests use the full projected laser segment.

**Technique:** near-miss gameplay should be derived from the same geometric collision contract as
damage, otherwise visual "graze" and actual collision drift.

## 17. Player hitbox can be smaller than body box

Direct-hit AABB can shrink a player's collision region using the custom HITBOX attribute.

Graze uses the wider inflated region.

Therefore the battle model has three conceptually distinct geometric envelopes:

```text
visual player body
direct danmaku hitbox
graze proximity envelope
```

Commit `e5fbe5735a2280d83b812b97392936b235e5ee51` fixes the hitbox-delta sign/attribute path.

**Technique:** bullet-hell hitbox is a gameplay contract, not necessarily the Minecraft entity box.

## 18. Mover architecture is an analytic trajectory DSL

Every `DanmakuMover` receives:

`MoverInfo(tick, previousPosition, previousVelocity, self)`

and returns:

`ProjectileMovement(translation, rotation)`.

### RectMover

Absolute position:

`p + v*t + 0.5*a*t^2`

Useful for:

- straight bullets
- acceleration/deceleration
- stop/reverse phases

### PolarMover

Adds a polar component around a moving rectangular center.

State includes:

- center position/velocity/acceleration
- radial distance/velocity/acceleration
- angle/angular velocity/angular acceleration
- plane normal/forward axes

Useful for:

- spirals
- rotating rings
- expanding/contracting patterns
- moving pattern centers

### CompositeMover

Time-sequences multiple movers.

This directly expresses:

```text
aim in place
 -> accelerate outward
 -> orbit
 -> leave on straight line
```

### ZeroMover

Translation = zero while orientation interpolates.

Useful for telegraph/wind-up.

### Attached movers

Bind projectile position/orientation to a holder/player.

Useful for:

- attached beams
- rotating emitters
- player-following spell geometry

**Technique:** use closed-form movement pieces whenever possible. Hundreds of bullets should not
need individual steering AI.

## 19. Projectile movement and visual facing are separate

`ProjectileMovement` stores both:

- movement vector
- rotation vector

`FixedDirMover` can use one mover for translation and a different fixed direction for rendering.

This is useful for decorative/rotating bullets whose visual orientation should not equal velocity.

## 20. Spell Cards are small schedulers, not giant tick methods

`ActualSpellCard` owns:

- card-local tick
- hit counter
- list of `Ticker<?>` jobs

Every tick it:

- increments card tick;
- ticks each job;
- removes jobs that report completion.

Locator:
- `spell/spellcard/ActualSpellCard.java#L21-L40`

A pattern can therefore start several independent subpatterns without writing one huge phase switch.

## 21. Ticker is a serializable mini-coroutine

A `Ticker<T>` stores its own integer tick and returns whether it has completed.

Pattern code commonly:

- creates a Ticker subclass;
- stores its parameters as serialized fields;
- sets negative tick for delayed start;
- emits bullets each local tick;
- self-removes when finished.

**Technique:** turn timed pattern fragments into stateful objects rather than spreading timing
variables across the boss entity.

## 22. ListSpellCard gives hit-count phases

`ListSpellCard` owns a list of `ActualSpellCard`.

When the current card's `hit` count reaches a threshold (default health=20):

- advance index;
- wrap after final phase;
- reset the new/current card.

Movement command delegation and damage-source semantics forward to the active phase.

This is a simple reusable boss spell-phase mechanism independent from vanilla health phases.

## 23. TrailAction: projectile death is a pattern event

`ItemDanmakuEntity.terminate()` executes `afterExpiry` if present.

That TrailAction can spawn another projectile/laser at the final position/direction.

Patterns can chain TrailActions.

Example class of behavior:

```text
gray bullet decelerates
       ↓ expires
purple homing bullet
       ↓ expires
fast colored terminal bullet
```

This appears in Reimu's spell implementation.

**Technique:** bullet expiry is not merely cleanup; it is a first-class event in the pattern graph.

## 24. ShooterEntity creates autonomous emitters

`ShooterEntity` is a lightweight LivingEntity that:

- has owner + target;
- has a lifetime and health;
- can move using a DanmakuMover;
- owns a SpellCard;
- renders a spell circle;
- implements `CardHolder`.

Therefore a spell pattern can spawn **emitters that themselves emit patterns**.

This is much more expressive than forcing all bullets to originate at the boss.

## 25. CardHolder makes pattern code reusable across actors

`CardHolder` abstracts:

- center
- forward direction
- target position
- target velocity
- random source
- bullet/laser preparation
- shoot operation
- damage
- independent shooter creation

Implementations can represent:

- Youkai mobs
- player spell holders
- ShooterEntity
- compatibility integrations

**Technique:** patterns depend on an emitter capability/interface, not a concrete boss class.

## 26. Representative authored patterns

### Reimu

Uses:

- distance-adaptive parameters
- ring/border patterns
- staged deceleration
- TrailAction transformations
- target-position homing
- fast/far target interception logic

The pattern uses geometry + staged movers rather than homing AI on every bullet.

### Marisa

Chooses attack family based on:

- distance
- target horizontal speed
- randomness

Examples:

- Master Spark: attached beam slowly rotates toward live target while emitting secondary bullets;
- Earth Light: terrain-aware laser spawn positions around target;
- Black Hole: rotating moving spawn points plus downward acceleration.

### Clownpiece

Combines:

- delayed Ticker start
- rotating radial projectiles
- lifespan-driven conversion to blue/red lasers
- homing or fixed TrailAction variants.

### Koishi

Uses:

- parametric laser curves
- radial bursts
- target-velocity border behavior
- a gameplay boundary that can constrain distant targets.

These show that the system supports authored "attack grammar", not merely radial bullet spam.

## 27. Custom Ring spell form

`RingSpellFormData` exposes:

- branch count
- step count
- delay
- branch angle
- per-step angle
- vertical step angle
- random angle
- first/last speed
- randomized speed

`RingSpellForm.tick()` converts these parameters into emitted directions.

This supports:

- ring
- flower
- fan
- random spread

with one reusable form.

**Technique:** expose high-level pattern topology as data rather than exposing raw projectile code.

## 28. Custom Homing form

The homing form is actually staged movement.

Stage 1:

- bullet launches outward;
- decelerates to zero over `turnTime`.

Then a Ticker waits for the turn point.

Stage 2:

- direction is recomputed from turn position toward target;
- a new bullet is spawned;
- it accelerates up to final speed.

This produces a visible "go out, stop/turn, home" behavior without continuous homing steering.

**Technique:** many visually homing patterns can be cheaper and more readable as **discrete
retarget stages**.

## 29. Graze is a battle economy, not only a near-miss score

`GrazeCapability` stores per-player:

- power
- hidden graze accumulation
- conversion step
- bomb shards
- life shards
- invulnerability
- weak/forbid state
- active Youkai combat sessions

Current key constants:

- 100 internal units per power level
- 5 shards per life/bomb
- 3-step resource conversion cycle
- temporary graze queue cap 10
- weak period 60 ticks

Graze first builds power. After max power it contributes to life/bomb resources.

## 30. Grazing is smoothed over time

Originally graze rewards were applied immediately.

Commit `df0612a47894975cbfe7b56daacdc2c1232caa4f`
("smooth out grazing") introduces `tempGraze`.

A graze event increments the queue up to 10.
Each player tick consumes from the queue according to graze effectiveness.

**Technique:** dense near-miss events can be coalesced into a bounded temporal accumulator instead
of making every collision sample immediately mutate/synchronize resource state.

## 31. Invulnerability and grazing are explicitly separated

Commit `963f95d6b233ddff41c7666299e86d5ab1409bfd`:

- blocks graze reward while invulnerable;
- makes the graze event cancelable;
- keeps client feedback packet separate.

This avoids farming graze from bullets that are temporarily non-threatening.

## 32. Spell-card battle sessions

When a full-character player enters battle:

- GrazeCapability adds a `CombatSession` for the Youkai;
- player UUID becomes one of the Youkai's targets;
- multiple sessions can coexist;
- sessions are cleaned when Youkai dies/disappears/no longer targets the player.

The player damage policy then uses the session set.

This makes "bullet hell battle" a temporary game mode layered on ordinary Minecraft combat.

## 33. Hit -> erase -> bomb/life transition

When Youkai-owned danmaku hits a player, `YoukaiEntity.danmakuHitTarget` asks
`GrazeCapability.performErase`.

Conceptually:

```text
danmaku hit
   |
   +-- invulnerable -> ignore damage
   |
   +-- active battle
         |
         +-- erase participating danmaku
         |
         +-- bomb available -> spend bomb, invul
         |
         +-- else power loss
               |
               +-- life available -> spend life, reset bomb, invul
               |
               +-- no life -> LAST / session reset path
```

`HitType` explicitly says whether:

- damage should be skipped;
- bullets should be erased.

**Technique:** bullet clear should be a first-class transaction result, not an ad-hoc loop in every
spell.

## 34. Bulk erase is owner/session aware

`YoukaiEntity.eraseAllDanmaku(player)` walks its owned virtual bullets.

- global clear can erase everything;
- player-scoped erase can preserve projectiles owned by the same player through
  `SimplifiedProjectile.erase(user)`.

GrazeCapability can request erasure across every active battle session.

This gives bombs/life loss a consistent field-clear semantic.

## 35. Danmaku invulnerability semantics

Current `IYHDanmaku.hurtTarget` checks existing hurtTime and last damage source.

For players/Youkai (and optionally other targets via config), another danmaku hit during the
relevant invulnerability window can be suppressed when the last direct source was IYHDanmaku.

The public 2.1.2 release history says danmaku damage was changed to bypass ordinary cooldown while
preventing one entity from being hurt twice; current implementation has evolved since that release.

**Boundary:** preserve the semantic requirement, not an old release implementation verbatim.

## 36. Laser lifecycle

Laser setup distinguishes:

- prepare period
- growth/setup
- active hit period
- ending/shrink period

Server hit test is active only in its configured window.

Client visual `effectiveLength` can clip against the first block hit.

**Technique:** beam telegraph, active damage, and disappearance should be distinct time windows.

## 37. Fading is gameplay readability

Projectile renderer can fade:

- the player's own bullets near camera;
- distant danmaku;
- all danger visuals during player invulnerability.

The renderer therefore supports both performance/readability and combat-state communication.

Do not assume "maximum visual opacity" is always best in dense patterns.

## 38. Historical performance evolution

### 2025-05-06 — performance boost

Commit `71ddd1e43f8d944feac6ae358372567fca1456a3`:

- adds ticking-region cleanup;
- caches projectile item stack access;
- avoids redundant base renderer calls.

### 2025-05-07 — user section cache

Commit `f1da61322d564afa5629bfb79b1b736636cd4aef`:

- introduces `IEntityCache`;
- adds shooter-local section matrix;
- projectile/laser collision selects per-shooter cache when possible.

### 2025-05-07 — virtual

Commit `6e01004fb1a7e749a5195a890bb1e76b8b54e384`:

- formalizes virtual client danmaku;
- ticks virtual bullets explicitly;
- adds explicit erase synchronization.

### 2.3.15

Commit `aa20f6e6d27e7765541a3b6e60ac352369714b06`:

- strips more generic baseTick work;
- changes spawn sync from per-bullet packet to batched list packet;
- records release note "Optimize danmaku rendering".

### 2026-04-09

Commit `2bb02d3433b558c5bc63ac201865ca8550caec4e`:

- fixes crash with ImmediatelyFast;
- keeps direct BufferBuilder write only when compatible.

## 39. Collision repair evolution

### 2025-02-10

`e35ff324...` fixes stuck danmaku by refusing to keep moving server projectiles into unloaded
chunks.

### 2025-02-10 / 11

`4cb84d2...` and `4faaa69...` progressively add moving-target collision sampling and broader
candidate bounds.

**Lesson:** dense projectile engines must define behavior at:

- loaded-chunk boundary;
- target high-speed boundary;
- owner/client tracking boundary.

## 40. Current source anomaly: TargetTracker velocity

Current `TargetTracker.vel()` returns:

`t2.subtract(t2).scale(0.1)`

which is always zero.

This expression exists back to the class's early history.

Reimu code contains branches that expect non-zero tracker velocity, e.g. choosing orientation based
on moving target velocity.

- expression always returning zero: **DIRECT_OBSERVATION**
- classification as unintended predictive-tracking bug: **INFERENCE**
- runtime symptom: **NOT_REPRODUCED**

**Lesson:** highly expressive pattern DSLs still need focused deterministic unit tests for small
math helpers.

## 41. Testing boundary

The repository has `src/test` Java/resources, but the enumerated tests are chiefly:

- generators
- resource organizers
- color/data utilities

No focused automated suite was found for:

- danmaku collision
- virtual packet lifecycle
- grazing
- pattern movers
- render batching
- performance regression.

No runtime benchmark was performed in this study.

## 42. Compatibility boundary of virtual bullets

Because many NPC bullets are not normal Level-managed entities:

- generic mods scanning `level.getEntities` may not see them;
- generic projectile hooks may not fire unless integrated deliberately;
- removal/tracking has to be handled by the owner/cache/packet layer;
- compatibility code must target the danmaku API boundary rather than assume normal EntityManager
  membership.

This is the main semantic price paid for virtualization.

## 43. Recommended reusable abstractions for KNEEKURA

### VirtualProjectileSwarm

```text
owner
active projectiles
spawn staging
erase
server tick
spawn batch
client cache
```

### ProjectileBroadphaseCache

```text
lifetime = one server game tick
section cache
optional owner-local section matrix
query(AABB)
```

### TrajectoryProgram

```text
MoverInfo(tick, previous position, previous velocity, actor)
 -> ProjectileMovement(translation, rotation)
```

### PatternScheduler

```text
SpellCard
  tick
  hit counter
  Ticker jobs
  expiry TrailActions
  optional child ShooterEntity
```

### BulletHellCollisionProfile

```text
directHitbox
grazeEnvelope
moving-target sweep/sample
invulnerability semantics
multipart unwrapping
```

### BattleSession

```text
participants
resources
invulnerability
target permissions
erase transaction
end/reset policy
```

## 44. What is most valuable for KNEEKURA

1. Virtualizing dense temporary entities while retaining object semantics.
2. Owner-local/manual ticking instead of global world registration.
3. Batched creation sync.
4. Type-grouped render submission.
5. Tick-scoped spatial collision caches.
6. Moving-target collision sampling.
7. Analytic/composable trajectory programs.
8. Mini-coroutine spell scheduling.
9. Projectile expiry as pattern continuation.
10. Emitter abstraction independent of boss/player/shooter.
11. Server-authoritative graze/bomb/life rules.
12. Separate direct hitbox vs graze envelope.
13. Explicit unsafe optimization fallback.
14. Focused phase/trajectory testing as a needed improvement.

## 45. Primary source locators

Pinned root:
https://github.com/Minecraft-LightLand/Youkai-Homecoming/tree/6d5744269aa597370a265d5c20eeb69902629441

Core:

- `dev/xkmc/fastprojectileapi/entity/SimplifiedEntity.java`
- `.../SimplifiedProjectile.java`
- `.../BaseProjectile.java`
- `.../BaseLaser.java`
- `.../collision/ProjectileHitHelper.java`
- `.../collision/LaserHitHelper.java`
- `.../collision/EntityStorageCache.java`
- `.../collision/UserMatrixCache.java`
- `.../render/virtual/ClientDanmakuCache.java`
- `.../render/virtual/DanmakuToClientPacket.java`
- `.../render/core/ProjectileRenderHelper.java`
- `.../render/core/BulkDataWriter.java`
- `content/entity/danmaku/IYHDanmaku.java`
- `content/entity/danmaku/ItemDanmakuEntity.java`
- `content/entity/danmaku/ItemLaserEntity.java`
- `content/entity/youkai/YoukaiEntity.java`
- `content/capability/GrazeCapability.java`
- `content/capability/GrazeHelper.java`
- `content/spell/mover/*`
- `content/spell/spellcard/*`
- `content/spell/game/*`
- `content/spell/custom/*`

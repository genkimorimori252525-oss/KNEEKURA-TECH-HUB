# Youkai's Homecoming — bounded Danmaku failure / repair history

## Scope

Focused history of projectile collision, virtual simulation/rendering, grazing and compatibility.

Pinned final source:
`6d5744269aa597370a265d5c20eeb69902629441`

No historical bug was reproduced at runtime in this study.

## 1. Stuck/out-of-chunk projectile

Commit:
`e35ff324ad13c34b05543155c97eef72f38a93fb`
— "fix stuck danmaku problem"

Before:
- movement proceeded even when the next server position left loaded chunk state.

Repair:
- lifetime termination happens before ordinary movement;
- server checks target/current chunk availability;
- projectile is discarded before continuing into unloaded space.

Later performance work also checks entity-section ticking state.

**Reusable lesson:** ephemeral projectile lifetime must include a **simulation-availability
boundary**, not only age and collision.

## 2. High-speed target collision — first repair

Commit:
`4cb84d297148eb7771b84f06b9f6d5e37197d4c5`
— "fix collision"

Repair:

- reads target velocity;
- computes number of target-position samples from target speed;
- tests projectile segment against multiple translated target AABBs;
- maximum initially four samples.

**Lesson:** projectile swept collision alone is insufficient when the target itself moves a large
distance per tick.

## 3. High-speed collision — refinement/shared laser logic

Commit:
`4faaa691208247718cc203a20aff23efcb7fbf20`
— "improve collision"

Repair:

- broadphase considers target AABB expanded toward target velocity;
- target narrowphase is extracted into shared `checkHit`;
- projectile and laser use the same moving-target logic;
- sampling becomes max 8 with roughly one sample per 0.5 target-speed units.

Release notes describe improved collision against high-speed entities.

**Lesson:** broadphase and narrowphase must agree about motion. Improving only the final segment
test cannot recover a target that broadphase never returned.

## 4. Performance pass before virtualization

Commit:
`71ddd1e43f8d944feac6ae358372567fca1456a3`
— "performance boost with danmaku"

Relevant changes include:

- server projectile ticking-region cleanup;
- projectile ItemStack caching;
- removal of redundant `super.render` work from danmaku/laser renderers.

**Lesson:** dense systems benefit first from deleting generic work that is harmless for one entity
but repeated hundreds of times.

No benchmark is attached to this history record.

## 5. Per-shooter section collision cache

Commit:
`f1da61322d564afa5629bfb79b1b736636cd4aef`
— "user section cache"

Repair/optimization:

- creates `IEntityCache` abstraction;
- adds `UserCacheHolder`;
- adds 11³ lazy section matrix centered on emitting entity;
- projectile/laser queries use shooter cache when owner supports it;
- cache is rebuilt by ServerLevel + gameTime.

**Lesson:** swarms share spatial locality. Cache candidate lookup at the emitter/tick level rather
than the projectile level.

## 6. Virtual projectile lifecycle

Commit:
`6e01004fb1a7e749a5195a890bb1e76b8b54e384`
— "virtual"

Observed changes:

- virtual projectile client package formalized;
- client virtual bullets explicitly advance old position/tick;
- erase packet added;
- SimplifiedProjectile distinguishes Level-managed vs virtual erase;
- Youkai manually ticks owned virtual bullets.

**Lesson:** once an object leaves the host entity manager, all lifecycle edges become explicit:
tick, spawn sync, erase sync, age/interpolation and owner tracking.

## 7. Virtual erase semantics repaired

Commit:
`f6dca4b2730a58241c3a866650bfec26cbf5efd4`

Observed:

- erase packet gains `kill` flag;
- projectile erase becomes idempotent;
- poof/visual kill effect is separated from silent lifetime cleanup;
- owner collection changes to LinkedList + temporary spawn list, avoiding mutation while iterating.

**Lesson:** "removed" and "destroyed with player-visible effect" are different lifecycle events.

## 8. 2.3.15 spawn batching / simplified tick work

Commit:
`aa20f6e6d27e7765541a3b6e60ac352369714b06`

Changelog:
- "Optimize danmaku rendering"
- "Add grazing sound effect"

Source changes relevant to dense projectiles:

- `SimplifiedEntity.baseTick` drops additional generic entity work;
- `DanmakuManager.send` becomes list-based;
- `DanmakuToClientPacket` carries an array of projectile descriptors;
- custom spawn payload bytes for the whole batch are concatenated into one buffer;
- Youkai queues new projectiles and sends once after danmaku pass.

**Lesson:** once simulation is virtualized, packet-per-projectile becomes the next obvious overhead.

## 9. Grazing added to shared collision layer

Commit:
`769b00df64e11dc9a61dc852cabf7887a7643e49`
— "graze"

Observed:

- `GrazingEntity` interface added;
- projectile/laser broadphase includes graze radius;
- direct hit checked first;
- near-miss check follows;
- projectile and laser get different per-projectile graze cooldowns;
- DanmakuGrazeEvent introduced.

**Lesson:** near-miss mechanics belong in geometry/collision infrastructure, not individual spell
implementations.

## 10. Grazing smoothing

Commit:
`df0612a47894975cbfe7b56daacdc2c1232caa4f`
— "smooth out grazing"

Before:
- graze immediately mutated reward progression.

After:
- bounded `tempGraze` queue;
- one or more queued units are consumed per player tick.

**Lesson:** coalesce high-frequency contact events into a bounded accumulator before economy/state
mutation.

## 11. Invulnerability graze fix

Commit:
`963f95d6b233ddff41c7666299e86d5ab1409bfd`
— "invul graze fix"

Repair:

- checks GrazeCapability invulnerability before posting/rewarding;
- makes DanmakuGrazeEvent cancelable;
- graze resource update becomes capability-owned.

**Lesson:** collision proximity does not imply reward eligibility. Gameplay-state authority must
gate geometric events.

## 12. Render fade/pass repair

Commit:
`2730a4f49ee0221ce12ccb8fa83578a2b723caa8`
— "render changes"

Observed:

- fixes fade alpha direction;
- normal danmaku SOLID route becomes transparent;
- laser per-instance fade colors are precomputed;
- core/outer pass submission is consolidated.

**Lesson:** render optimization cannot be separated from visual-state correctness. Batching a wrong
alpha state only makes the wrong result faster.

## 13. ImmediatelyFast crash

Commit:
`2bb02d3433b558c5bc63ac201865ca8550caec4e`
— "fix danmaku rendering crash with ImmediatelyFast"

Before:
- BulkDataWriter wrote directly into BufferBuilder internals whenever consumer type matched.

After:
- detect `immediatelyfast`;
- force standard VertexConsumer path under that mod;
- retain direct fast path otherwise.

**Lesson:** implementation-internal buffer writes must be treated as an optional fast path with a
public-contract fallback.

This is a strong compatibility pattern for the TECH-HUB optimization lane.

## 14. Danmaku hitbox attribute sign fix

Commit:
`e5fbe5735a2280d83b812b97392936b235e5ee51`
— "danmaku hitbox shrink effect fix"

Observed:

- helper renamed from "shrink" to "delta";
- direct-hit AABB applies negated configured delta;
- related equipment attributes adjusted.

**Lesson:** gameplay hitbox modifiers need tests that assert the resulting geometric envelope, not
only an attribute value.

## 15. Current predictive tracker anomaly

Current source:

`TargetTracker.vel()` -> `t2.subtract(t2).scale(0.1)`

This is mathematically always zero.

The same expression is present in earlier tracked revisions of that file.

Reimu pattern code contains paths expecting non-zero tracker velocity.

Evidence state:

- zero-return expression: **DIRECT_OBSERVATION**
- "bug" classification: **INFERENCE**
- player-visible reproduction: **NOT_RUN**
- repair: **NOT_FOUND**

**Lesson:** trajectory/prediction helpers deserve small deterministic mathematical unit tests.

## 16. Test/benchmark coverage gap

The repository contains test-source utilities, generators and resource organizers.

This review did not find a focused automated regression suite for:

- moving-target danmaku collision
- graze envelopes
- virtual bullet spawn/erase lifecycle
- mover trajectories
- render batching
- ImmediatelyFast fallback
- performance metrics.

No runtime benchmark is claimed.

## Coverage status

**PARTIAL / SOURCE-HISTORY-BACKED**

Covered:
- source at final 2.7.0
- collision repair commits
- virtual lifecycle commits
- render batching/compatibility repair
- graze evolution
- hitbox repair
- current tracker anomaly

Not established:
- exhaustive issue/PR history
- exact released JAR/source binary equality
- measured FPS/MSPT/allocation benefits
- every spell pattern's historical evolution
- runtime reproduction of current anomaly

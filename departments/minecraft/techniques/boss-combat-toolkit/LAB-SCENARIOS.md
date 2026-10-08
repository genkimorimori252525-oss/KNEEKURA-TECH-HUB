# Boss Combat Toolkit v1 — LAB Scenarios

These scenarios are designed for the KNEEKURA Minecraft LAB / Water Tank style of
bounded observation. They are **not** proof of any particular upstream MOD's
runtime performance.

## Measurement channels

For each scenario capture, where available:

- server MSPT/TPS;
- boss state + attack state/age;
- position/velocity;
- target id/distance;
- entities spawned/alive;
- projectiles spawned/alive;
- block edits attempted/succeeded;
- relevant entity-query result counts;
- packets/messages per tick or bounded proxy count;
- client frame time/FPS where client testing is enabled;
- persistent FX live counts;
- cancellation/error reason.

Keep gameplay metrics and visual metrics separate.

## LAB-BCT-01 — lifecycle soak

Purpose: detect attack state leaks.

Setup:

- one boss;
- one durable target;
- all adopted attacks enabled;
- no artificial event spam.

Run:

- enough time for every attack type to enter/exit several times;
- periodically force target loss/reacquire if harness permits.

Pass:

- no attack remains stuck beyond declared maximum duration;
- no cooldown becomes negative/unbounded;
- resource locks return to zero/idle between attacks;
- entity/FX counts return toward baseline.

## LAB-BCT-02 — max-range beam

Purpose: measure worst-case continuous beam cost.

Setup:

- unobstructed arena at maximum supported beam range;
- one target near far endpoint;
- comparison run with early obstruction.

Compare:

- server tick cost;
- beam work/sample count if instrumented;
- network update rate;
- client render cost.

Pass:

- work is bounded by configured maximum;
- obstructed case shortens authoritative geometry;
- no gameplay difference from client detail setting.

## LAB-BCT-03 — projectile storm

Purpose: stress projectile and presentation budgets.

Setup:

- run the highest-entity-count legal attack to completion;
- record projectile population curve;
- repeat with impact clustering.

Pass:

- spawn count matches bounded design;
- projectile lifetime prevents permanent accumulation;
- camera/screen effects respect caps/aggregation;
- persistent FX collection stays within budget.

## LAB-BCT-04 — deflection chamber

Purpose: verify ownership and attribution under repeated reflection.

Setup:

- deterministic projectile source;
- two eligible deflectors;
- original owner and allied/non-allied targets.

Cases:

- no deflection;
- one deflection;
- repeated deflection;
- deflection near original owner;
- deflection near new owner;
- projectile lifetime edge.

Pass:

- owner/team/damage attribution matches BCT-D;
- no immortal lifetime-reset loop;
- no unexplained self/friendly collision.

## LAB-BCT-05 — faction-density sweep

Purpose: measure temporary-faction acquisition/AI cost.

Run the same boss with increasing nearby eligible mob counts, for example:

- 0;
- 16;
- 64;
- 128 or the LAB-safe maximum.

Capture:

- query count;
- overlay acquisitions/releases;
- server tick cost;
- target-selection cost;
- member count;
- cleanup after owner removal.

Pass:

- scan remains bounded;
- no stale overlay after release;
- cost curve is documented before raising production limits.

## LAB-BCT-06 — persistent FX saturation

Purpose: prove client queues are finite.

Generate events beyond each adopted FX capacity.

Pass:

- live count plateaus at/below cap;
- eviction order matches policy;
- old records expire;
- setting capacity to zero/minimum has defined behavior;
- combat results remain identical.

## LAB-BCT-07 — multi-boss presentation

Purpose: verify audio/presentation priority and cleanup.

Setup:

- two or more bosses in different phases;
- move player in/out of presentation range;
- kill/remove higher-priority boss.

Pass:

- selected music/loop follows documented priority;
- transition is deterministic;
- removed boss leaves no ghost loop;
- lower-priority state resumes/terminates as designed.

## LAB-BCT-08 — semantic death interruption

Purpose: protect platform lifecycle from long cinematics.

Cases:

- normal kill;
- kill during attack TELEGRAPH;
- kill during beam ACTIVE;
- kill with controlled faction members alive;
- kill during high client FX load.

Pass:

- death/killer/loot/XP semantics occur once according to product contract;
- visual death may continue only without resurrecting semantic life;
- attacks stop producing unauthorized new damage;
- controller/faction cleanup is deterministic.

## Performance acceptance rule

Do not declare a toolkit module "fast" from one aggregate soak.

Record the exact scenario, limits, entity density, client count, machine/runtime
identity and percentile/summary metric used by the product.

A product may accept a module with a known cost, but the cost must remain visible.

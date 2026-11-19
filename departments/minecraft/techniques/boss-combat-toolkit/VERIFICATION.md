# Boss Combat Toolkit v1 — Verification Contract

Toolkit adoption is not complete when code compiles. Each module has explicit
verification gates. Products may add stricter tests.

## Evidence levels

- **STATIC** — source/bytecode/config relationship is established.
- **UNIT** — pure logic contract is tested without a full Minecraft runtime.
- **GAMETEST** — dedicated Forge runtime verifies server gameplay semantics.
- **LAB** — bounded instrumented scenario measures interaction/performance.
- **VISUAL** — client presentation is reviewed in a controlled scene.
- **ACCEPTED** — product-specific acceptance criteria are met.

A build success cannot be promoted to runtime or performance evidence.

## Common mandatory tests

### V-COMMON-01 — cancellation releases state

Interrupt every interruptible attack during TELEGRAPH and ACTIVE.

Pass:

- attack leaves no held movement/look/attack resource;
- no future damage occurs from the cancelled attack unless already committed
  projectiles are intentionally independent;
- cooldown/recovery follows documented policy;
- debug snapshot converges to a non-active state.

### V-COMMON-02 — target loss

Remove/kill/change-dimension the target at each lifecycle state.

Pass:

- no null/infinite-retry loop;
- product policy (cancel/continue/reacquire) is deterministic;
- no stale client loop or beam persists.

### V-COMMON-03 — boss removal/death

Remove or semantically kill the boss during each active presentation type.

Pass:

- server gameplay ends according to product death semantics;
- client loops/FX eventually stop;
- temporary faction ownership is released or follows documented persistence;
- no duplicate loot/XP/death event.

### V-COMMON-04 — read-only observability

Pass:

- debug snapshot reports active attack/state/age/target/cooldown;
- observing does not mutate gameplay state;
- snapshot remains bounded in size.

---

## BCT-A Attack Lifecycle

### V-A-01 — legal transition graph

Attempt every legal and illegal transition.

Pass:

- only declared state edges occur;
- illegal edge is rejected or mapped to explicit cancel/recovery;
- cooldown cannot be bypassed by repeated start requests.

### V-A-02 — arbitration conflict

Start two attacks requiring the same resource.

Pass:

- exactly one owns the conflict or documented preemption occurs;
- no simultaneous duplicate damage caused by an arbitration race.

### V-A-03 — phase transition during attack

Change phase during TELEGRAPH and ACTIVE.

Pass:

- behavior matches declared cancel/finish/upgrade policy;
- transition action occurs exactly once.

---

## BCT-B Beam

### V-B-01 — obstruction

Place a solid obstacle between boss and target.

Pass:

- authoritative beam length ends at the configured collision boundary;
- target beyond obstacle receives no beam hit.

### V-B-02 — visible-length/client independence

Manipulate/delay client beam state in a test harness without changing server beam.

Pass:

- server damage remains unchanged;
- client eventually converges when current state is received.

### V-B-03 — bounded maximum range

Run beam at maximum configured range.

Pass:

- per-tick algorithm respects declared maximum;
- no search/sample continues beyond the limit;
- performance scenario is separately recorded in LAB.

---

## BCT-D Projectile Deflection

### V-D-01 — ownership transfer

Deflect a projectile once.

Pass:

- new owner/attribution follows contract;
- projectile damages allowed original-side target;
- projectile respects new friendly-fire relation.

### V-D-02 — repeated deflection

Deflect up to and beyond the supported deflection limit.

Pass:

- limit is enforced or repeated deflection remains deterministic;
- lifetime is not accidentally reset forever.

### V-D-03 — near-owner/self-hit

Test collision immediately after deflection near both old and new owner.

Pass:

- collision grace/assist follows explicit contract;
- no unexplained immunity or instant self-hit.

---

## BCT-F Temporary Faction

### V-F-01 — acquire/release

Apply overlay, let it expire, then inspect entity.

Pass:

- controller relation active only during interval;
- overlay Goals/effects are removed;
- original entity identity remains;
- cooldown state follows contract.

### V-F-02 — controller invalidation

Kill/unload/change dimension of controller.

Pass:

- controlled mob leaves overlay or follows documented persistence;
- no dangling runtime entity reference.

### V-F-03 — ally matrix

Test controller ↔ member, member ↔ member, member ↔ outsider.

Pass:

- alliance and target filters match the declared matrix;
- same-controller members do not acquire each other unless explicitly allowed.

---

## BCT-X Client FX Budget

### V-X-01 — capacity

Generate more events than `max_live`.

Pass:

- collection never exceeds declared bound;
- eviction policy is deterministic;
- gameplay remains unchanged.

### V-X-02 — expiry

Create FX and stop new events.

Pass:

- all records expire by declared lifetime;
- no orphan tick/render work remains.

### V-X-03 — disabled/detail mode

Set FX to disabled/minimum detail.

Pass:

- optional visual workload falls;
- server combat results are identical.

---

## BCT-P Boss Presentation

### V-P-01 — presentation priority

Spawn multiple bosses/states that compete for music/presentation.

Pass:

- documented priority wins deterministically;
- lower-priority source resumes or terminates according to policy.

### V-P-02 — loop cleanup

Start ambient/attack loops then remove source.

Pass:

- loops terminate in bounded time;
- no ghost sound follows a removed entity.

### V-P-03 — event storm aggregation

Generate dense projectile/impact events.

Pass:

- camera/screen effect remains within declared cap;
- intensity does not scale unboundedly with event count.

---

# Acceptance matrix template

Products should maintain a table like:

| Test ID | STATIC | UNIT | GAMETEST | LAB | VISUAL | Result/evidence |
|---|---|---|---|---|---|---|
| V-COMMON-01 | | | | | | |
| V-A-01 | | | | | | |
| V-B-01 | | | | | | |
| ... | | | | | | |

Only the columns relevant to adopted modules are required.

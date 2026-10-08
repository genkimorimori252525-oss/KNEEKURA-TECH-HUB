# Boss Combat Toolkit v1 — Module Contracts

This file defines what each reusable module must mean regardless of the product's
concrete Java class names.

## BCT-A — Attack Lifecycle

### Purpose

Make major attacks independently schedulable, cancellable, observable and testable.

### Canonical states

```text
IDLE
  ↓ eligibility + arbitration
TELEGRAPH
  ↓ commit point
COMMITTED
  ↓
ACTIVE
  ↓
RECOVERY
  ↓
COOLDOWN
  ↓
IDLE
```

An implementation may merge states, but it must still expose equivalent semantic
boundaries.

### Required product-owned fields

- attack id;
- eligibility result;
- rejection reason;
- current semantic state;
- state age;
- chosen target or target snapshot;
- committed direction/position if relevant;
- cooldown remaining;
- cancellation reason;
- resources/locks held by the attack.

### Invariants

- only the server changes gameplay attack state;
- TELEGRAPH may retarget only if the product explicitly allows it;
- after COMMITTED, the policy for retarget/cancel must be explicit;
- ACTIVE work is bounded per tick;
- stop/cancel must release attack resources;
- recovery and cooldown are not inferred from animation completion;
- save/reload behavior is explicit for long attacks.

### Arbitration

Products should define a stable answer for:

- can two attacks run concurrently?
- does movement conflict with attack?
- does target loss cancel, downgrade or continue?
- can a higher-priority attack preempt?
- does phase transition cancel current attack?
- what happens on stun/death/unload?

A useful implementation model is named resource locks such as:

- `MOVE`
- `LOOK`
- `PRIMARY_ATTACK`
- `SECONDARY_ATTACK`
- `WORLD_EDIT`

Minecraft Goal flags may implement this, but the contract is independent of
GoalSelector.

---

## BCT-B — Beam Contract

### Purpose

Separate authoritative continuous-hit geometry from visual beam presentation.

### Server owns

- beam origin;
- aim vector/angles;
- max range;
- obstruction rule;
- sample/raycast algorithm;
- entity intersection;
- hit cadence;
- damage/effects;
- authoritative visible length;
- start/stop.

### Client owns

- interpolation;
- mesh/beam rendering;
- texture;
- particles;
- attack-loop sound;
- optional light/screen effects.

### Minimum synchronization state

One of:

```text
attack instance id
origin reference
aim vector/angles
visible length
active flag / sequence number
```

or an equivalent compact form.

### Invariants

- client beam length never grants damage;
- server hit logic is deterministic for a fixed tick snapshot;
- maximum work per active tick is bounded;
- obstruction policy is testable;
- multi-hit vs first-hit behavior is explicit;
- friendly-fire/team filtering is explicit;
- stale packet/state cannot resurrect a stopped beam.

---

## BCT-D — Projectile Deflection

### Purpose

Represent a projectile changing sides as a change of authority/allegiance, not
merely a velocity reflection.

### Required state

- current owner;
- owner team/faction relation;
- deflectable flag;
- deflection count;
- last deflector;
- new direction/velocity;
- post-deflection damage policy;
- collision grace/assist policy;
- lifetime remaining.

### Canonical transition

```text
HOSTILE(owner=A)
  -- valid deflection by B -->
TRANSFER(owner=B, last=A)
  -->
HOSTILE_TO_A / FRIENDLY_TO_B
```

The implementation may mutate the existing projectile or replace it with a new
one. The observable semantics should be the same.

### Invariants

- kill/damage attribution follows the post-deflection owner policy;
- repeated deflection is bounded or explicitly supported;
- self-hit and original-owner hit rules are explicit;
- friendly-fire rules are explicit;
- deflection cannot reset lifetime indefinitely unless intentionally designed;
- reflected projectiles cannot silently bypass server authority.

---

## BCT-F — Temporary Faction Overlay

### Purpose

Temporarily attach an existing mob to a boss encounter without replacing its
EntityType.

### State

- controller/owner UUID;
- controller runtime id when needed for client sync;
- start tick;
- expiry tick/duration;
- post-release cooldown;
- original team/faction relation if it must be restored;
- overlay AI state;
- presentation state.

### AI overlay responsibilities

Possible overlays include:

- follow controller;
- defend controller;
- copy controller target;
- acquire controller enemies;
- avoid friendly fire;
- temporary attributes/effects.

### Invariants

- owner invalid/dead/unloaded policy is explicit;
- max separation policy is explicit;
- release restores or cleanly removes overlay state;
- AI overlay cannot survive after ownership state is cleared;
- temporary allies do not accidentally attack each other;
- save/reload and dimension-change behavior is explicit;
- attachment scope is no broader than necessary.

### Compatibility seam

Prefer data tags/config for:

- cannot be controlled;
- immune to faction overlay;
- remains hostile;
- no-follow/no-teleport;
- special boss exclusions.

---

## BCT-X — Client FX Budget

### Purpose

Ensure valid gameplay events cannot create unbounded client presentation work.

### Every persistent FX family defines

- key/type;
- max live count;
- lifetime;
- eviction policy;
- distance culling;
- visibility culling;
- detail/quality scalar;
- disabled state;
- update frequency;
- worst-case creation rate.

### Recommended eviction

Use one explicit policy:

- oldest first;
- farthest first;
- lowest priority first;
- per-source quota + global cap.

Do not rely on garbage collection or natural scene exit.

### Invariants

- `max_live = 0` has defined behavior;
- no unbounded collection growth;
- server does not serialize every visual particle;
- presentation degradation cannot change gameplay;
- attack storms aggregate rather than multiply screen-space effects without cap.

---

## BCT-P — Boss Presentation

### Purpose

Centralize visual/audio encounter state without making it combat authority.

### Presentation state may include

- spawn/intro;
- normal combat;
- phase/finale;
- stun;
- special attack loop;
- death/outro.

### Audio classes

Keep distinct:

- one-shot cue;
- entity-following loop;
- attack loop;
- music;
- transition stinger.

### Required policy

When multiple bosses/presentation sources exist, define deterministic priority
and replacement/fade behavior.

### Invariants

- combat state exists independently of music/animation completion;
- no sound loop survives source removal;
- stop/unload/death releases client state;
- packet loss/stale state converges to current server state;
- camera shake/screen effects are capped and range-aware;
- presentation can be disabled/reduced without changing combat.

---

# Shared Debug Snapshot

Any product adopting BCT-A plus one other module should expose a read-only
snapshot containing at least:

```text
boss id/type
phase/state
active attack id
attack lifecycle state + age
target id
position/velocity
cooldowns
beam state if any
live boss-owned projectiles
temporary-faction member count
persistent FX counters (client-side where observable)
last cancellation/transition reason
```

The snapshot is for observation only; it is not a hidden control API.

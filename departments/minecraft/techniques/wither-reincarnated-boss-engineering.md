# Boss Engineering Patterns Recovered from Wither: Reincarnated

Status: **REUSABLE TECHNIQUE NOTE**  
Anchor examined: Minecraft 1.20.1 / Forge / Wither: Reincarnated 1.0.5  
Artifact receipt: `../mods/wither-reincarnated/ANALYSIS-RECEIPT-2026-10-08.json`

This note contains independent engineering patterns derived from static analysis.
The upstream artifact is **All Rights Reserved**. No code/assets are reproduced.

## P1 — attack modules need a common lifecycle

Represent each major boss move with the same conceptual contract:

```text
eligible?
can continue?
start
tick
stop
cooldown/recovery
resource/flag ownership
```

The implementation may use Minecraft Goals, a custom state machine, Brain
memories, or another scheduler. The important part is that attack arbitration is
explicit and observable.

Benefits:

- easier priority/conflict reasoning;
- attack-specific tests;
- safer cancellation;
- clearer debug telemetry;
- lower chance of unrelated attacks sharing hidden timers.

## P2 — a beam should have one combat authority

For continuous beams:

1. server owns origin, aim, obstruction, hit test and damage;
2. server derives a compact visible length/state;
3. client interpolates and renders;
4. client sound/particles follow the received state;
5. visual interpolation never decides damage.

This avoids client/server divergence and prevents networking every sample point.

## P3 — projectile deflection is an ownership transition

A projectile that becomes the defender's attack should transition:

```text
old owner -> deflection event -> new owner/team -> new trajectory -> new hit policy
```

Do not model this only as `velocity = -velocity`.

Tests should verify:

- attribution after deflection;
- friendly fire;
- boss/self collision;
- damage variant;
- repeated deflection;
- lifetime;
- save/reload if projectiles can persist.

## P4 — temporary encounter factions can overlay existing mobs

For possession/charm/conversion mechanics, keep the original entity and apply an
encounter overlay when possible:

- controller UUID/entity id;
- active interval;
- cooldown;
- ally relation;
- target/follow Goals;
- temporary attributes/effects;
- client presentation.

This preserves third-party mob identity while allowing temporary boss ownership.

Risk: attaching a full capability to every Mob is convenient but may be broader
than necessary. Prefer a narrow attachment/lookup strategy when scope is known.

## P5 — compatibility exceptions should be data-driven

Expose tags/data for categories such as:

- boss will not target;
- cannot be possessed/charmed;
- does not flee;
- blocks excluded from destruction;
- biomes/dimensions excluded from travel;
- projectiles that participate in an interaction.

This gives modpacks a compatibility seam without Java patches.

## P6 — network presentation state, not rendering work

Prefer packets that transmit small semantic events/state:

- attack start;
- beam orientation/length;
- controller/owner relationship;
- explosion point;
- camera impulse envelope.

Then reconstruct:

- animation;
- particles;
- beams;
- music;
- looped sounds;
- screen shake

on the client.

Use dimension/tracking-range scoping and explicit protocol/version identifiers.

## P7 — persistent client FX require a budget

Every long-lived visual family should have:

- bounded live count;
- lifetime;
- eviction;
- distance/visibility culling;
- detail control;
- optional disable switch.

A rare boss barrage is exactly where unbounded client presentation lists are most
likely to fail.

## P8 — aggregate screen effects during event storms

Projectile storms can generate many logically valid impact events but should not
produce linearly stacking camera shake.

Use:

- attack-level envelopes;
- capped accumulation;
- temporal de-duplication;
- spatial aggregation;

so presentation cost/intensity remains bounded.

## P9 — audio is a state machine

Boss audio should distinguish:

- one-shot cues;
- entity-following ambient loops;
- attack loops;
- encounter music;
- phase/finale music;
- outro.

When multiple bosses exist, define a deterministic priority rule. Do not let the
last arbitrary tick win.

## P10 — test worst-case attack slices independently

Do not rely on average encounter TPS.

Measure isolated slices such as:

- max-range beam;
- max entity-density ownership scan;
- full projectile barrage;
- block-destruction burst;
- multiple bosses;
- multiple tracking clients.

Record server tick cost, allocations/entity count, packet rate and client frame
impact separately.

## P11 — architecture must match product scope

A vanilla-overhaul MOD may reasonably patch global vanilla classes.

A standalone KNEEKURA boss should prefer:

- independent EntityType;
- owned state machine;
- owned renderer;
- owned projectile types;
- explicit compatibility adapters.

Global Mixins are a scope decision, not a reusable default.

## P12 — replacing behavior requires a legacy-policy checklist

Whenever a custom boss replaces a vanilla policy, review the old sources one by
one:

- damage;
- healing;
- loot/XP;
- death events/removal;
- target selection;
- navigation;
- invulnerability;
- block destruction;
- sounds/music;
- renderer/client hooks.

Suppress only what is truly replaced. This is particularly important for healing
and death lifecycle, where duplicated or bypassed vanilla behavior can break
compatibility invisibly.

## Provenance boundary

These patterns are derived from class/resource/bytecode observation of the exact
artifact named in the receipt. They may be independently implemented, but the
upstream ARR code/assets are not stored or copied.

## Promotion into the reusable toolkit

The portable parts of P1–P12 have now been normalized into the product-neutral
[Boss Combat Toolkit v1](boss-combat-toolkit/README.md).

This file remains the **source-specific derivation note**: it explains what was
learned from Wither: Reincarnated. The toolkit is the reusable contract and is
intentionally free of Reincarnated gameplay constants.

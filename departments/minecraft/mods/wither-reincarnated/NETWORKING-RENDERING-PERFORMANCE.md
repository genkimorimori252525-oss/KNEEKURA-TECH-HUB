# Wither: Reincarnated — Networking, Rendering and Performance Surfaces

Evidence basis: exact v1.0.5 ANCHOR JAR
`00589726de7d82628d92761394a8a3e6b153c28942f50c9ae6ba7860b0fab80a`.

This is a static architecture/cost analysis. No profiler or packet capture was run.

## 1. Network contract

The MOD registers six dedicated clientbound message classes:

1. `ClientboundShakeCameraPacket`
2. `ClientboundStartLaserPacket`
3. `ClientboundUpdateLaserPacket`
4. `ClientboundUpdatePossessedMobPacket`
5. `ClientboundWitherSkullBlastPacket`
6. `ClientboundWitherStartAnimationPacket`

The helper `Messages.sendToAllPlayers(MSG, Level)` resolves the target from the
Level's dimension and uses a dimension-scoped distributor rather than treating the
entire server as one audience.

### Design lesson

Send authoritative gameplay results from the server, but synchronize only the
small presentation state needed by the client.

Examples in this binary:

- laser: entity id + beam orientation/length state;
- attack animation: entity id + compact animation selector;
- possession: mob/owner identity + timers/state;
- skull blast: event position rather than a replicated particle cloud;
- camera shake: event parameters rather than camera transforms.

The client reconstructs the expensive visual/audio state locally.

## 2. Laser: authoritative hit test, client beam

The laser is a strong example of server/client separation.

Server:

- owns target tracking and ray sampling;
- resolves obstruction;
- resolves LivingEntity intersection;
- applies damage/effect;
- computes final beam length.

Client:

- stores current/previous angle and length;
- interpolates presentation state;
- renders the beam;
- drives laser-specific sound/particle presentation.

This avoids making visual interpolation part of the combat authority.

### Transfer rule

For a custom beam attack, synchronize:

- attack instance/entity id;
- origin/angle or target vector;
- authoritative visible length;
- start/stop state.

Do not synchronize every intermediate ray sample or every beam vertex.

## 3. Compact attack animation events

`ClientboundWitherStartAnimationPacket` carries a small selector rather than a
serialized animation graph. Client `HandleAnimationsEvent` owns the local
AnimationState objects and timers.

This pattern reduces packet shape and keeps animation implementation client-only.

Risk: numeric selectors become opaque if they are not documented. An independent
implementation should use a named enum/protocol version instead of undocumented
magic integers.

## 4. Possession synchronization

Possession is a persistent server-side gameplay state and therefore sends more
than a one-shot effect.

The client update contains enough identity/timing information to render the
possessed state without deciding whether the mob is actually possessed.

This is the correct authority direction:

```text
server capability / owner state
        ↓
compact state packet
        ↓
client overlay + FX
```

The renderer never becomes the source of truth.

## 5. Renderer composition

The Wither presentation is decomposed into a custom renderer/model plus separate
layers/effects rather than one monolithic render method.

Observed components include:

- `BetterWitherRenderer`
- `BetterWitherSkullRenderer`
- `BetterWitherModel`
- `BetterWitherArmorLayer`
- `BetterWitherExplodingLayer`
- `BetterWitherGlowLayer`
- `BetterWitherNetherStarLayer`
- `PossessedLayer`

The client registration path replaces the vanilla Wither/WitherSkull renderer for
this global overhaul and appends possession rendering to LivingEntity renderers.

### Transfer rule

Layer composition is reusable.

Global replacement of vanilla renderers and injection into every
LivingEntityRenderer is **not** a default recommendation for a standalone boss.
Prefer registering layers/renderers only for owned entity types unless the feature
really must affect arbitrary third-party mobs.

## 6. Audio state machine

The MOD separates:

- spawn/intro music;
- normal fight music;
- powered/finale music;
- outro/death music;
- continuous normal/weak ambient loops;
- laser-specific attack audio.

Music choice is client-side and driven by Wither state. The selected state also
has explicit priority when multiple Withers are present.

Reusable lesson: boss music is a presentation state machine, not a sequence of
uncoordinated `playSound` calls.

A reusable implementation should define:

```text
NONE < OUTRO < INTRO < COMBAT < FINALE
```

or another explicit priority policy, then centralize fade/replace behavior.

## 7. Long-lived visual effect budgets

`ParticleSpawnersEvent` keeps client-side collections for long-lived effects:

- SmokeColumn
- DistantFire

Client config exposes:

- `max_distant_fire`
- `max_smoke_columns`
- detail scalars;
- opacity/color controls;
- optional falling ash.

The observed default configuration uses finite caps rather than allowing the
collections to grow without bound.

### Reusable pattern

For persistent boss debris/embers/smoke:

1. represent the effect as a cheap client-side record;
2. give it an explicit lifetime;
3. keep a configurable global or encounter-local capacity;
4. evict oldest entries when capacity is exceeded;
5. make detail independent from simulation/gameplay;
6. allow `0` to disable expensive optional layers where practical.

This is more robust than creating an unbounded particle source per explosion.

## 8. Camera shake under projectile storms

Camera shake is event-driven and range-sensitive. The MOD also contains logic to
avoid treating every skull in a dense barrage as an independent full-strength
shake source.

Reusable lesson: screen-space effects need aggregation/de-duplication under high
event rates.

For a barrage, prefer:

- one encounter/attack shake envelope;
- or bounded accumulation with a maximum intensity;

rather than `N projectiles × full shake`.

## 9. Static cost surfaces

These are inspection-derived stress points, **not measured performance results**.

### Laser

Configured max length 128 with a 0.25 step gives an upper spatial sampling scale of
roughly 512 samples in an active tick before entity/block intersection work.

### Possession

The Wither possession path queries a living-entity region based on a 64-block
inflated AABB. Large entity counts can therefore dominate the cost more than the
random possession probability itself.

### Terrain destruction

The encounter periodically scans a bounded cuboid around the Wither. Even bounded
loops should preserve Forge destruction hooks and should not be expanded casually.

### Barrage

An uninterrupted barrage can create roughly 180 skull entities over its firing
window. Entity count, collision, explosion and client effects all compound.

### Network

Active laser state is updated repeatedly while the attack runs. Dimension scoping
is helpful, but independent implementations should additionally consider
tracking-range scoping and rate reduction if visual quality allows.

## 10. What KNEEKURA should adopt

Recommended concept-level recovery:

- server-authoritative combat/client-derived presentation;
- dimension/tracking-aware event distribution;
- compact attack-state packets;
- interpolation of visual-only state;
- composable render layers;
- explicit music/sound state machines;
- finite queues/lifetimes for persistent client FX;
- aggregation of camera effects under projectile storms;
- dedicated performance scenarios for high-entity-count attacks.

Do not copy the packet classes, render code, textures, models, sounds or numeric
encodings from the ARR artifact.

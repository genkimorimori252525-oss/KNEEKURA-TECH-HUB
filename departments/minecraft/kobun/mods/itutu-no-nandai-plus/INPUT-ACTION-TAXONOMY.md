# INPUT-ACTION TAXONOMY — 五つの難題MOD+ X1

Status: MODERN-EXTRACTION derived from ORIGINAL_SOURCE / ORIGINAL_BINARY

The X1 combat system separates surprisingly well into two orthogonal layers:

1. projectile/effect language — rings, lasers, homing, special shots, controllers;
2. input/action resolution — Shift, hold time, physical state, context and item state.

The same projectile language is selected by many different input conditions.

## Action pattern A — FOCUS

Modifier narrows an angularly ambiguous pattern.

Examples:

- Homing Amulet
- generic THShot cone/fan/ring
- generic THLaser random-ring/fan/ring

Useful modern contract:

focusHeld -> narrower spread, optionally different projectile count/damage profile

## Action pattern B — TOPOLOGY_SWITCH

Modifier chooses a different geometric family.

Examples:

- Hourai Branch: forward nested rings -> omnidirectional circles
- Yuyuko Fan: forward mirrored fans -> full circles
- Dragon Neck Jewel: single carrier -> five-carrier fan

This is stronger than changing one scalar.

## Action pattern C — VERB_SWITCH

Modifier chooses a different interaction verb.

Examples:

- Hakurouken: BRAKE vs REFLECT
- Death Scythe: PULL vs PUSH
- Kappa Pistol: FIRE vs REFILL when context permits

The action resolver should return a semantic verb, not just a numeric mode.

## Action pattern D — CONTINUOUS_CHARGE_SCALAR

heldTicks maps to one continuous parameter.

Examples:

- Roukanken -> dash power
- Tengu Fan -> shot speed
- Miko Sword -> scan radius
- Yuyuko/Hourai -> density
- Yuuka Parasol -> radial launch magnitude

## Action pattern E — THRESHOLD_LADDER

Hold duration selects discrete capabilities.

Sanae Oharaibou is the clearest case: 30/60/90/120/150 ticks choose successively stronger miracle-card charging opportunities.

## Action pattern F — EMBODIED_CHARGE

Charge state lives in a visible world entity.

Examples:

- Onmyoudama grows in front of player
- NuclearShot grows in front of player
- AjaRedStoneEffect accumulates visible/environmental power
- MiracleCircle shows ritual stages

This directly telegraphs stored power.

## Action pattern G — CONTEXT_ACTION

Buttons are insufficient to decide the action.

Examples:

- Kappa Pistol checks source water
- Sukima checks ray hit, distance and entity/block target
- Aja samples block light
- ItemTHLaser inspects adjacent dye
- Dragon Jewel checks durability

Recommended modern resolver input:

InputContext
- focusHeld
- useTicks
- grounded
- velocity
- airborne
- lookVector
- rayHit
- selectedSlot
- neighboringSlots
- persistentItemMode
- itemCondition
- environmentSamples
- targetFacts
- resourceState

## Action pattern H — PERSISTENT_MODE

Input changes future meaning of the item.

Examples:

- Sakuya Watch half/stop mode
- deployed Yuuka Parasol mode cycle

A mode toggle should be distinct from fire intent.

## Action pattern I — PHYSICAL_STATE_GATE

Movement state changes whether an action is valid or modifies its effect.

Examples:

- Roukanken ground-only dash
- Hakurouken ground+moving brake
- WIND01 airborne victim bonus
- Yuuka Parasol falling-only descent damping

## Action pattern J — OUTPUT_CHANNEL_VARIANT

Action changes how information is presented without changing the world effect.

Miko Sword sneak suppresses chat while keeping DivineSpirit markers.

## Action pattern K — INTERRUPT / FAILURE SEMANTICS

Charge can be interrupted into a distinct result.

Nuclear Control Rod turns item switching during held charge into an explosion.

A modern system should explicitly model:

- release
- cancel
- item switch
- death
- invalid target
- context override

rather than assuming every use ends by normal release.

## Recommended resolution pipeline

InputContext
  -> ActionVariant resolver
  -> CombatIntent
  -> projectile/effect/controller execution

CombatIntent should carry:

- action verb
- geometry profile
- projectile/effect profile
- ownership rules
- charge value / threshold tier
- selected target / ray result
- resource cost
- cancel/interruption behavior

The projectile system should not need to know which key selected the intent.

## Priority / conflict rules

X1 contains useful examples of why explicit priority matters.

- Kappa Pistol: successful refill consumes the action before firing.
- Sakuya Watch: Shift toggles mode and returns before normal use.
- Dragon Jewel: durability can invalidate a requested variant.
- Sukima: close targets are rejected for the long-pair mode.
- Nuclear Shot: item switching is not normal release; it is a different terminal state.

A modern resolver should encode these priorities intentionally.

## False-affordance rule

Do not infer gameplay from the presence of an input branch alone.

Examples:

- Hakurouken computes unused charge size.
- Bloodthirsty Onmyoudama ignores hold duration.
- Onmyoudama armor sneak movement code is commented.
- Houtou attack/focus code is dormant.

Evidence must reach the effect-producing path.

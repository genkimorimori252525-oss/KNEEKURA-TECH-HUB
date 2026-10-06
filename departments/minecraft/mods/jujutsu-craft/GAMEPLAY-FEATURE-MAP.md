# Gameplay feature map

## Technique dispatch

Major character technique selection is largely procedure-driven from persistent skill IDs rather than independent item classes.

### Gojo

`CursedTechniqueGojoProcedure` includes:

- 205 Infinity
- 206 Blue
- 207 Red
- 208 Blue Punch
- 215 Hollow Purple
- 220 Unlimited Void

### Sukuna

Core dispatch includes:

- 105 Dismantle
- 106 Cleave
- 107 Open
- 120 Malevolent Shrine

Additional IDs route to later/alternate techniques.

## Defense / neutralization vocabulary

The MOD has explicit shared systems for:

- Infinity
- Domain Amplification
- Simple Domain
- Hollow Wicker Basket
- Falling Blossom Emotion
- Reverse Cursed Technique
- domain battle / sure-hit handling
- Mahoraga adaptation
- technique neutralization

Entity tags expose capability membership rather than forcing every check through Java class identity.

## Persistent field techniques

Several iconic techniques are represented as persistent world entities/fields:

- Blue
- Red
- Purple
- Domain Expansion actors
- Malevolent Shrine
- Mahoraga / shikigami actors

This supports ongoing area influence, animation and repeated attack logic instead of one-tick damage calls.

## Domain Expansion

A generic shared barrier/lifecycle layer handles coordinates, cover, battle state, start/failure/defeat and anti-domain interactions. Character-specific behavior is dispatched on top.

## Ten Shadows

A common procedure coordinates Divine Dogs, Rabbit Escape, Agito, Mahoraga and related ownership/domain state.

## Black Flash

Black Flash is integrated into generic attack resolution. Successful stochastic escalation spawns its own entity/particles/sounds/effects and progression state.

## Reverse Cursed Technique

RCT is effect-driven and supports self-use/output semantics, curse-power cost, fatigue and cursed-spirit polarity handling.

## World / progression

The artifact includes extensive structures, biome modifiers, advancements, loot and profession/technique menus. Gameplay progression and combat are therefore coupled to world content rather than being a combat-library-only mod.

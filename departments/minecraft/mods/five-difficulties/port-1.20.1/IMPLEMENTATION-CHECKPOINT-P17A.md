# Implementation checkpoint — P17a danmaku-mob core, fairies, familiar

Date: 2026-11-20
Oracle: X1 `EntityDanmakuMob`, `EntityTHFairy`, `EntitySunFlowerFairy`, `EntityFamiliar`, `DanmakuPatternRegistry`,
`THShotLib.banishExplosion`, `ModelTHFairy`, `ModelSunFlowerFairy`, `RenderTHFairy`, `RenderSunFlowerFairy`,
`RenderFamiliar`, `CommonProxy` (registration, eggs, spawns).

## Ported

| X1 | Port |
|---|---|
| `EntityDanmakuMob` | `entity/mob/DanmakuMobEntity` |
| `DanmakuPatternRegistry` | `core/x1/X1DanmakuPatterns` (built for the configured danmaku level) |
| `EntityTHFairy` / `EntitySunFlowerFairy` / `EntityFamiliar` | `THFairyEntity`, `SunFlowerFairyEntity`, `FamiliarEntity` |
| models / renderers | `client/mob/THFairyModel`, `SunFlowerFairyModel` (boxes generated from the X1 constructors), `P17Renderers` |
| spawn eggs, `addSpawn` | `th_fairy_spawn_egg`, `sunflower_fairy_spawn_egg`; biome modifiers `th_fairy_spawns`, `sunflower_fairy_spawns` |

## X1 behaviour kept on purpose

- Base mob: health 2, speed 0.25, follow 30; peaceful removes it; danmaku level 0 drops the target. With no
  target it wanders; with one it hovers `flyingHeight` above the ground (+0.006 a tick when lower, toward the
  target's height when higher), faces it, fires `danmakuPattern` each tick it can see it, loses it after 200
  unseen ticks, and keeps its attack distance with cos-eased moves. Flying mobs move with air drag 0.91 and no
  gravity. Hits it takes go through the magic-damage reduction twice (X1 calls `applyPotionDamageCalculations`
  before `super`). Bat sounds at 0.3 volume and 1.95 pitch; spell card drop when killed by a player while
  using one; death blast at death tick 7 that hurts fairies within 5 (at least 2).
- `getSpecies_1/2` return SPECIES_OTHERS in the base class whatever `setSpecies` stored (X1).
- Fairy: 0.6 × 1.5, 5 XP, form 0..2, random table pattern, speed 0.3, attack and detection 8, flying 2;
  fires when its counter wraps at the pattern span (sphere / wide / circle / random ring / ring / laser
  sphere families decoded from the pattern number); calls fairies within 30 to its target. In the nether or
  on 31 October it does not die: it sinks and returns as a zombie fairy. Drops (player kills): small red shot
  items, power and point bonuses; more for 10-HP fairies.
- Spawn rules: config switches, `fairySpawnRate`, rarer below y 64, sky light above 7, grass / dirt / sand.
- Sunflower fairy: 0.9 × 1.7, 20 HP, 30 XP, form 10, spawns with a familiar riding it; its fairy drops plus
  medium green shots, bonuses, 5 % extend or else 25 % spell-card bonus.
- Familiar: rides a mob, fires as the first non-familiar down the riding chain, takes its target, vanishes
  without a shooter; no sounds, drops or collision. Rendered as a spinning inverted-add disc.
- Model quirks kept: children's pivots are relative to their parent (the fairy's long hair hangs at chest
  height); `mirror = true` written after `addBox` mirrors nothing; dead fairies' heads are set to 70 rad.

## Mapping notes

- 1.7.10 biomes folded into their 1.20 successors (e.g. extreme hills → windswept hills, ice plains →
  snowy plains; the hill variants into their base biomes).
- Halloween is read from the server clock, as X1 read `World.getCurrentDate`.

## Receipts

Dedicated server (local; P5–P17 together, 11 scenarios PASS twice in a row, 0 FAIL):

```
FIVE_DIFFICULTIES_P17_FAIRY_PASS shots=1
FIVE_DIFFICULTIES_P17_BANISH_PASS
FIVE_DIFFICULTIES_P17_SUNFLOWER_PASS
FIVE_DIFFICULTIES_P17_RUNTIME_SCENARIO_PASS
```

## Not covered yet

- Real-client frame for the fairies (with the next P17 step).

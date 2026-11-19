# Implementation checkpoint — P16a small items

Date: 2026-11-20
Oracle: X1 `ItemHeavenlyPeach`, `ItemSwallowCowrieShell`, `ItemClosedThirdEye`, `ItemTenguFan`, `ItemOnbashira`,
`ItemHouraiPearl`.

## Ported

| X1 | Port |
|---|---|
| `ItemHeavenlyPeach` | `heavenly_peach` (`X1SmallItems.HeavenlyPeach`) |
| `ItemSwallowCowrieShell` | `swallow_cowrie_shell` |
| `ItemClosedThirdEye` | `closed_third_eye` |
| `ItemTenguFan` | `tengu_fan` |
| `ItemOnbashira` | `onbashira` |
| `ItemHouraiPearl` damage 0..7 | `hourai_pearl_<colour>` ×8 (white is not in the creative tab, as X1 lists seven) |

## X1 behaviour kept on purpose

- Peach: food 2, meat, always edible, stack 10, Resistance level 2 for 400 ticks.
- Cowrie shell: never used up and gives no normal food; up to 10 levels become hunger (2 per level,
  saturation 5) and Regeneration II for 3 s per level; standing, only as much as the hunger bar is missing.
- Closed third eye: Invisibility for 20 ticks; mobs within 30 that cannot see the player or are more than 8
  away drop them as a target. Returns pass (not consumed).
- Tengu fan: durability 40, use 24 ticks; on release a FORM_WIND / AQUA / WIND01 shot (end 20) at
  (24 − left) / 7; holding the full 24 ticks blows nothing.
- Onbashira: wooden sword, digs everything at 3, 5..22 extra mob damage per hit, slows sideways and upward
  motion ×0.9 every tick while carried anywhere.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_FOOD_PASS resistance=2 levels=25 food=20
FIVE_DIFFICULTIES_P16_EYE_PASS nearSees=true
FIVE_DIFFICULTIES_P16_FAN_PASS speed=2.000
FIVE_DIFFICULTIES_P16_ONBASHIRA_PASS dealt=16.728
FIVE_DIFFICULTIES_P16_RUNTIME_SCENARIO_PASS
```

## Not covered

- In-world client frame for these items (textures only checked by the importer hashes).
- TechHub Tank: a refmap-remapped mapped-dev jar is built (`gradlew jar -x reobfJar` + SRG→official refmap
  rewrite), but the host lock left by the earlier failed trial blocks a new trial; release is pending.
- The remaining P16 items with their own entities.

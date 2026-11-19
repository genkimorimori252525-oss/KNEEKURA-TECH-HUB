# Implementation checkpoint — P16b weapons without their own entity

Date: 2026-11-20
Oracle: X1 `ItemSpearTheGungnir`, `ItemLaevateinn`, `ItemRoukanken`, `ItemRoukanSenpuuzin`, `ItemDeathScythe`,
`ItemKaigo`, the tool materials in `THKaguyaItems`.

## Ported

| X1 | Port (`X1Weapons`) |
|---|---|
| `ItemSpearTheGungnir` | `spear_the_gungnir` |
| `ItemLaevateinn` (laevateinn 0/95/9/3) | `laevateinn` |
| `ItemRoukanken` (roukanken 0/251/4/3) | `roukanken` |
| `ItemRoukanSenpuuzin` | `roukanken_senpuuzin` |
| `ItemDeathScythe` (iron, 444) | `death_scythe` |
| `ItemKaigo` (kaigo 0/1/0/−4, unbreakable) | `remorse_rod` (+ `used` model override) |

## X1 behaviour kept on purpose

- 1.7.10 swords deal 4 + material damage; the port uses an attack modifier of 4 (Onbashira from P16a corrected
  from 3 to 4 to match).
- Gungnir: declares card 27 (level 2) and throws a GUNGNIR laser (width 1, length 10, damage 14, end 120) from
  0.6 above the eyes at the look vector with x and z negated, as X1 passes it; `setItemDamage(+1)` never breaks it.
- Laevateinn: sets the target on fire for 3..5 s; right-click sweeps a FIRE set laser (colour RED + 16, width 0.6,
  length 20.8, damage 7, end 30) around the player at −6°/tick (sneak: vertical, angle Z 90); only one per player
  within 20 blocks.
- Roukanken: webs and leaves 30, wool 20, everything else ×3, harvests anything; undead +16 with a magic crit;
  release on the ground to dash `min(held, 20) × 0.3` with 1.5 exhaustion; while selected and moving faster
  than 3 it cuts living things (undead 16, others 8) and splits non-laser enemy shots into three white
  half-size shots. As in X1 this runs on the side that sees the motion.
- Senpuuzin: glint, cuts within 1.5 at any speed, stops at the first target in hurt time, never wears.
- Death scythe: the far end of its 16-block line is measured from the feet (X1 quirk); pulls (sneak: pushes) the
  nearest living thing by 0.6.
- Remorse rod: knocks a target above 3/4 health to 3/4 once, then dull until right-clicked with an ink sac.
  X1's "damage 1" state is a `KaigoUsed` tag in the port.
- Senpuuzin has no name in X1's lang files; the port shows the same raw key.

## Receipts

Dedicated server (local; P5–P16 together, 3 runs in a row, 10 scenarios PASS each, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_GUNGNIR_PASS shots=1
FIVE_DIFFICULTIES_P16_LAEVATEINN_PASS
FIVE_DIFFICULTIES_P16_ROUKANKEN_PASS dash=3.0
FIVE_DIFFICULTIES_P16_SCYTHE_PASS
FIVE_DIFFICULTIES_P16_KAIGO_PASS
FIVE_DIFFICULTIES_P16B_WEAPONS_PASS
```

## Not covered

- In-world client frames for these weapons.
- TechHub Tank trials (blocked by the stale host lock; see P16a).

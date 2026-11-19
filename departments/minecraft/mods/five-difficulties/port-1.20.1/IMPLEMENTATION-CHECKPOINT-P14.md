# Implementation checkpoint — P14 bonus items, player power, extend, config

Date: 2026-11-19
Oracle: X1 `ItemTHPowerItem`, `ItemTHPointItem`, `ItemTHBombItem`, `ItemTHExtendItem`, `EntityTHItem`,
`EntityShotMaterial`, `RenderTHItem`, `THKaguyaPlayerDeathEventHandler`, `THKaguyaLib.getPlayerPower`,
`THKaguyaConfig`.

## Ported

| X1 | Port |
|---|---|
| `ItemTHPowerItem` (damage 0 small / 1 big), point, bomb (64), extend (8) | `power_item_small`, `power_item_big`, `point_item`, `bomb_item`, `extend_item` |
| `EntityTHItem` + `RenderTHItem` | `THItemEntity`, `THItemRenderer` |
| `EntityShotMaterial` | `ShotMaterialEntity` rewritten statement by statement (non-final, `check` / `moveToPlayer` hooks, the `lastTime` freeze) |
| `THKaguyaLib.getPlayerPower` | `X1PlayerEvents.getPlayerPower`, now feeding `THShotItem`'s damage (+ power / 400) |
| `THKaguyaPlayerDeathEventHandler` | `X1PlayerEvents.onLivingDeath` |
| `THKaguyaConfig` | `X1Config` (Forge COMMON config `five_difficulties_port-common.toml`) |
| bombs in `spellCardDeclaration` | `X1SpellCardDeclaration.bombItem` → `bomb_item` |

## X1 behaviour kept on purpose

- Power: small items count 1, big ones 10, over the main inventory, capped at 400.
- `EntityTHItem`: for 16 ticks it only drifts (×0.87 sideways, gravity 0.03 down to −0.2); afterwards the
  shot-material logic runs, but only a sneaking player draws it in (at 0.3). With no player within 20
  it vanishes; landing on top of a block removes it; X1's fall-through `switch` on the other faces is
  kept. Power and point items are lost when the inventory is full; bombs and extends drop instead.
- Every dying player plays "down" (Down Vol).
- Config: X1's categories, keys and defaults (Limit, Effect, SE vol, Danmaku, Other). Wired now: the
  spell-card, Master Spark and down volumes, Use Master Spark, Master Spark Destroys Blocks (shot
  explosions), Use default Gap SE (Enderman portal or `sukima`), Danmaku Level (Hanabeeper, Youryoku
  Spoiler). The mob options (spawns, accuracy, one-kill mode) arrive with the mobs; the chisel and
  recipe options with their items / recipes.

## Deliberate deviations

- The extend cancels the death. X1 heals the player inside the 1.7.10 death event without cancelling it,
  so `onDeath` (death message, inventory drop) still ran on a fully healed player.
- `defineInRange` resets an out-of-range Danmaku Level to its default 2, where X1 clamps it to 0..4.
- The "EntityID" category has no meaning in 1.20 and is not ported.

## Fixes found on the way

- P11 played the declaration sound at volume 1.0; X1 uses Spell Card Vol (0.5 by default).
- `ShotMaterialEntity` had dropped X1's `check` hook and the time-stop freeze (`lastTime`); both are back.

## Receipts

Dedicated server (local; P5–P14 together, 0 failures on the final run):

```
FIVE_DIFFICULTIES_P14_CONFIG_PASS danmakuLevel=2 spellCardVol=0.5
FIVE_DIFFICULTIES_P14_POWER_PASS small3big2=23 cap=400 shotBonus=0.1
FIVE_DIFFICULTIES_P14_EXTEND_PASS extendsLeft=1 invulnerable=100
FIVE_DIFFICULTIES_P14_BOMB_PASS bombsLeft=2 levels=0
FIVE_DIFFICULTIES_P14_ITEMS_PASS homingMin=0.82
FIVE_DIFFICULTIES_P14_RUNTIME_SCENARIO_PASS
```

- POWER: 3 small + 2 big = 23, capped at 400; a shot item fired with 40 power deals its base + 0.1.
- EXTEND: the death event is cancelled, the player is at full health with 100 ticks of invulnerability,
  one extend is used and a purple spell-card circle appears. (A fake player's `die()` is a no-op in
  Forge, so the scenario posts the same `LivingDeathEvent` a real player's death fires.)
- BOMB: with no levels and no bombs Mishaguji-sama is refused; with five bombs it is declared, three
  bombs are used and the levels stay at 0.
- ITEMS: a bonus next to a standing player drifts down and vanishes on landing; one next to a sneaking
  player comes within 0.82 and its bomb is picked up.

One of three local runs with P14 added failed P13's wind check (the husk was not knocked up within 20
ticks); the other runs passed it with the same numbers as before (hit after 5 ticks, knock-up 2.00).
The cause is not known yet; the check now reports the wind's and the husk's state if it fails again.

Real client (local, private overlay): `FIVE_DIFFICULTIES_P14_CLIENT_RESOURCES_PASS bonusItems=5`; the
in-world frame shows a big power bonus.

## Not covered

- Danmaku mobs drop these bonuses (`EntityDanmakuMob`, P17); here they are spawned directly.

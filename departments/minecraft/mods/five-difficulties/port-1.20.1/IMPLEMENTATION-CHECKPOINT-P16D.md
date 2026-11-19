# Implementation checkpoint — P16d effect-entity items (talisman, sutra scroll)

Date: 2026-11-20
Oracle: X1 `ItemSpiritualStrikeTalisman`, `EntitySpiritualStrikeTalisman`, `RenderSpiritualStrikeTalisman`,
`ItemMazinKyoukan`, `EntityMazinkyoukan`, `RenderMazinkyoukan`, `THKaguyaLib.itemEffectFollowUser`.

## Ported

| X1 | Port |
|---|---|
| `ItemSpiritualStrikeTalisman` (霊撃札) | `spiritual_strike_talisman` item (`X1EffectItems`) |
| `EntitySpiritualStrikeTalisman` + renderer | `SpiritualStrikeTalismanEntity`, `P16Renderers.SpiritualStrikeTalisman` |
| `ItemMazinKyoukan` (魔人経巻) | `sorcerer_sutra_scroll` item |
| `EntityMazinkyoukan` + renderer | `MazinkyoukanEntity`, `P16Renderers.Mazinkyoukan` |
| `itemEffectFollowUser` | `X1ItemEffects.followUser` |

## X1 behaviour kept on purpose

- Talisman: appears 2 ahead at 30° to the right (pitch-tilted, 0.5 below the eyes) and lives 4 ticks. Each tick
  everything within `ticks × 4` except the user and what the user rides is handled: living things that are not
  animals or villagers get motion `direction × power` with upward `0.5 × power`, power `(range − distance) × 0.1`;
  shots inside turn into their finish bonus. The user is not synced to clients, so the client copy pushes its
  own player too, as X1's did. The server sets motion without forcing a velocity packet, as X1.
- Talisman render: a spinning two-sided card (21°/tick, tilted 30°) and, with the time-stop effect on, an
  additive blue sphere of `ticks × 3` (max 240) at alpha 0.4.
- Sutra scroll: each right-click spawns a scroll that follows the user 0.5 ahead while the item is in use;
  `count` grows to 114 (turning 2.88°/tick after 50). On release `time = count / 3`; it costs `time / 8 + 1`
  levels (time −8 per missing level) and gives Speed V, Strength I, Jump Boost II and Resistance I for
  `time × 10` ticks. Rendered as `count` one-degree strips on a 1.6 ring with inverted-add colour cycling.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_TALISMAN_PASS push=0.440,0.264
FIVE_DIFFICULTIES_P16_SUTRA_SCROLL_PASS
FIVE_DIFFICULTIES_P16D_EFFECT_ITEMS_PASS
```

## Not covered

- The two renderers are compiled but not yet seen in a real client frame (planned at the end of P16).

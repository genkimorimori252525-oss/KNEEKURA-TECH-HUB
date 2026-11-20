# Implementation checkpoint — P18a Divine Spirit and the Toyosatomimi sword

Date: 2026-11-20
Oracle: X1 `BlockDivineSpirit`, `ItemBlockDivineSpirit`, `TileEntityDivineSpirit`, `TileEntityDivineSpiritRenderer`,
`RenderDivineSpiritBlock`, `EntityDivineSpirit`, `RenderDivineSpirit`, `ItemMikoSword`.

| X1 | Port |
|---|---|
| `divine_spirit` metadata 0..7 | `divine_spirit_{red,blue,green,yellow,purple,aqua,orange,white}` blocks + block items |
| `TileEntityDivineSpirit` (+ special renderer) | `DivineSpiritBlock.DivineSpiritBlockEntity`, `DivineSpiritRenderers.Block` |
| `EntityDivineSpirit` / `RenderDivineSpirit` | `divine_spirit` (`DivineSpiritEntity`), `DivineSpiritRenderers.Spirit` |
| `ItemMikoSword` (`toyosatomimi_sword`) | `MikoSwordItem` |

## X1 behaviour kept on purpose

- Block: glass-like, hardness 0.1, resistance 2000, snow sounds, light 8, no collision (full outline), not
  opaque, drops itself. X1's block renderer draws nothing; the tile renderer draws three MusouFuuin quads
  (alpha 0.3 / 0.7 / 1.0, ONE / ONE_MINUS_SRC_COLOR, no depth write) in the colour of its metadata, bobbing
  ±0.16 with time = world time + x·y·z, turned to the camera by the yaw / pitch of its offset, scale pulsing
  0.8 ± 0.16 with z squashed to 0. The tile entity itself holds nothing (all commented out in X1).
- Spirit entity: drifts toward the nearest player within 10 (+0.03 a tick up to 0.5; −0.03 when nobody is near,
  along its last heading), gone after 300 ticks, shrinks as it ages. Touching a player gives the matching block
  (pickup pop if it fits) and removes the spirit either way. Its renderer's yellow uses green 64 (block: 224).
- Sword: iron, no enchanting. Hold and release: up to ten nearest living things within the ticks held (≤ 50)
  each leave a spirit at eye height — fairy 85 % blue / 10 % green / 5 % purple, creeper green, villager blue,
  animal yellow (tamed: purple), water animal aqua, undead white, arthropod orange, otherwise red. Unless
  sneaking each is reported in chat (number, name, front / back / left / right, up / down past 3 blocks,
  distance; dark red for monsters, green for animals, dark aqua otherwise). One damage per spirit (not in
  creative); it only breaks on the next right-click at or past its maximum. The ±180° wrap after a bearing
  is computed adjusts the player's angle instead (X1 bug), kept.

## Deviations

- Metadata colours are separate blocks (1.20 has no block metadata).
- X1's item icons point at `textures/items/divinespirit_*`, which do not exist (missing-texture icons in X1),
  and three block icon names differ in case from the files; the port uses the block textures for both.
- Creative tab: X1 tabDecorations → Functional Blocks.

## Receipts

- Server: `FIVE_DIFFICULTIES_P18A_DIVINE_SPIRIT_PASS spirits=2` (block light / collision / drop; zombie → white,
  cow → yellow, 2 damage; touch gives the block), all P17 checks, P6/P8–P17 `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; the eight blocks seen as glowing coloured billboards (not committed); no
  missing-texture models.

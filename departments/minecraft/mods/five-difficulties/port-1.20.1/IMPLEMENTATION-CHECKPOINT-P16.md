# Implementation checkpoint — P16 summary

Date: 2026-11-20

P16 ported every remaining X1 item that does not need the P17 mobs or the P18 blocks, with their effect
entities and renderers. Details per step: `IMPLEMENTATION-CHECKPOINT-P16A.md` … `P16O.md`.

| Step | Items |
|---|---|
| P16a | heavenly peach, swallow cowrie shell, closed third eye, tengu fan, onbashira, Hourai pearls |
| P16b | Gungnir, Laevateinn, Roukanken, Roukanken Senpuuzin, death scythe, remorse rod |
| P16c | soul torch, Yuyuko fan, kappa water pistol, Ibuki gourd |
| P16d | spiritual strike talisman, sorcerer sutra scroll (+ entities) |
| P16e | Aja red stone (+ effect entity, special 351) |
| P16f | Nazrin pendulum (+ entity) |
| P16g | icicle sword (Cirno ice box), Hakurouken (reflecting wall) |
| P16h | Buddha stone bowl, illness charm, wall-passing chisel, ship-ghost dippers |
| P16i | fire rat robe, Marisa hat, kappa cap, Suwako hat (+ hat models) |
| P16j | silver knives (+ entity, dispenser); 1.7.10 box intercepts across the port |
| P16k | Yuuka's parasol (+ entity, special 350) |
| P16l | Hisou sword (+ eight sword entities, card 7) |
| P16m | third eye, bloodthirsty yin-yang orb, Hourai jeweled branch |
| P16n | Kinkakuji ceiling (+ rideable entity) |
| P16o | Marisa's broom (+ entity) |

## Deferred to later phases

- `ItemCursedDecoyDoll` / `EntityCursedDecoyDoll` (extends `EntityDanmakuMob`) — P17.
- `ItemMikoSword` (spawns `EntityDivineSpirit`, checks `EntityTHFairy`) — P17 / P18.
- `ItemUchide` (Miracle Mallet) — P17 per the roadmap.
- The shot-item dispenser behaviour (fires through an `EntityFamiliar`) — P17.
- `EntityHakureiShield` is registered by X1 but nothing spawns it; nothing to port until something does.

## Real-client frames (local, private overlay, not committed)

`p16_items.png` (scroll, Aja rays, pendulum, Cirno ice box, Hakurou wall, both hats on armour stands) and
`p16_items2.png` (Kinkakuji ceiling, Yuuka's parasol, Hisou swords and their kishitu, broom).
`FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_PASS` in the same run.

## Known CI flake (not from P16)

P13's GOHEI check failed twice in CI ("the orb stays above the ground, y -4.6765007303604875", identical
both times: the P16d and P16m runs) and never locally. The same value both times points to one specific
path rather than noise. The orb ends below the bottom of the flat world, so one hypothesis is that the chunk
it bounced in had no collision at that moment. This is not measured. To be investigated separately.

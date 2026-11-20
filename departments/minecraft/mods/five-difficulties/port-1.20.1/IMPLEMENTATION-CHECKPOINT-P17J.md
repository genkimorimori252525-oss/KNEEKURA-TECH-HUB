# Implementation checkpoint — P17j Miracle Mallet, cursed decoy doll, Hanabeeper spawns; roukanken texture

Date: 2026-11-20
Oracle: X1 `ItemUchide`, `ItemCursedDecoyDoll`, `EntityCursedDecoyDoll`, `ModelCursedDecoyDoll`,
`RenderCursedDecoyDoll`, `THKaguyaLib.itemEffectFinish`, `CommonProxy` (Hanabeeper).

| X1 | Port |
|---|---|
| `ItemUchide` | `miracle_mallet` (`X1MalletItems.MiracleMallet`) |
| `ItemCursedDecoyDoll` | `cursed_decoy_doll` item (`X1MalletItems.CursedDecoyDoll`) |
| `EntityCursedDecoyDoll` | `cursed_decoy_doll` entity (`CursedDecoyDollEntity`), `CursedDecoyDollModel`, `P17Renderers.Plain` |
| Hanabeeper egg 0x0FF080 / 0xC0C000, desert 2 (1–4) behind `spawnHanabeeper` | `danmaku_creeper_spawn_egg`, `danmaku_creeper_spawns` |

## X1 behaviour kept on purpose

- Miracle Mallet: with any food left, right-click grows every shot of yours within 20 by 0.5, plays the bow
  sound and adds 30 damage, with no cap and no break (1.7.10 `setItemDamage`); it heals 1 damage per
  inventory tick. Its GUI and item-transforming parts are commented out in X1, and the chest-loot hook is never
  registered, so neither exists here.
- Doll item: durability 30, glint. Does nothing while any doll is within 40; otherwise places one at the
  player and takes 1 damage. At 30 it becomes the item in its "OriginalItemID" tag, which only the
  commented-out mallet GUI wrote, so in practice it becomes nothing.
- Doll entity: still (speed 0, 40 HP, 1 XP). Each tick, for everything within 40 except its user, the user's
  mount, item frames and paintings: a creature that already has a target re-targets the doll; every living
  thing takes it as its revenge target. Another doll in range is finished, and so is this one. No player
  within 40 → finished; after 180 ticks → vanishes. "Finished" gives the user a fresh doll item
  (`itemEffectFinish`), so finishing hands back an extra doll; kept.
- Hanabeeper: the vanilla monster rule, and natural spawns only with `spawnHanabeeper` on (default off).

## Deviation

- X1 gives the doll entity no name (1.7.10 showed the raw key); it reuses the item's name here.

## Fix to P16

- `import-private-x1-assets.py` listed `roukanSword.png` twice in one dict; the second (for Senpuuzin)
  overwrote the first, so `item/roukanken.png` was never imported and the Roukanken showed the missing
  texture. One entry now; the Senpuuzin model uses `item/roukanken`. Client log: 0 missing-texture models.

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_MALLET_DOLL_PASS size=0.8`, all other P17 checks and P6/P8–P17
  `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; the doll inspected by eye in the P17 frame (not committed).

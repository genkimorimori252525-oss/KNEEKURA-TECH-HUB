# Implementation checkpoint — P17g Sakuya and Sanae (traders)

Date: 2026-11-20
Oracle: X1 `EntitySakuya`, `EntitySanae`, `ModelSakuya`, `ModelSanae`, `RenderTHBoss`, `CommonProxy`.

| X1 | Port |
|---|---|
| `EntityDanmakuMob implements IMerchant` (shared code) | `entity/mob/X1TraderMobEntity` (1.20 `Merchant`) |
| `EntitySakuya` | `sakuya` (`SakuyaEntity`), egg 0xC1C1D6 / 0x3053E7 |
| `EntitySanae` | `sanae` (`SanaeEntity`), egg 0x6BD245 / 0x2937E0 |
| `ModelSakuya` / `ModelSanae` | `client/mob/SakuyaModel`, `SanaeModel` (generated trees) |

## X1 behaviour kept on purpose

- Both start in `NOT_ATTACK`, where X1's `isEntityInvulnerable` is true; 1.7.10 `attackEntityFrom` then rejects
  every hit, and nothing moves them out of it. They are invulnerable traders; the boss plate is hidden
  (`RenderTHBoss` skips `NOT_ATTACK`). Their phase tables (Sakuya card 8; Sanae cards 14 / 17 / 18 / 16) are
  ported for completeness but are unreachable, as in X1. Sanae's normal star pattern (`danmaku01`) is only
  reachable from a normal phase that never happens, so it is not ported.
- Right-click (not with a spawn egg, not sneaking) opens the merchant screen titled with the mob's name.
- Offers: Sakuya 16 shot materials → silver knife (meta 0 = blue), 64 → Sakuya's stopwatch; Sanae
  64 → illness-recovery charm. 1.7.10's default 7 uses, never restocked (X1 commented the reset out), saved as
  "Offers". No trade XP (1.7.10 had none).
- Spawns: ambient, weight 1, in X1's 26 overworld base biomes (mapped to 1.20 names), 2 % of attempts, and not
  on a spot whose four neighbours below are all the same block as the one underfoot.
- `ModelSakuya` writes the body / skirt Y turn only while sneaking, so it sticks; kept. `ModelSanae` sets
  the arms again after drawing; the next frame's angles overwrite that first, so it never shows.
- Removed in peaceful like every X1 danmaku mob (X1 `EntityDanmakuMob.onUpdate`).

## Deviation

- 1.20 rejects a spawn group minimum of 0, so X1's 0–1 group is 1–1 here.

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_TRADERS_PASS sakuya=2 sanae=1` (no damage, offers, lock after 7, save / load),
  P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; P17 frame with Sakuya and Sanae inspected by eye (not committed).
- Not tested: opening the trade screen with a real player.

# Implementation checkpoint — P17i Rinnosuke

Date: 2026-11-20
Oracle: X1 `EntityRinnosuke`, `VillagerRinnosuke`, `ModelRinnosuke`, `RenderRinnosuke`, 1.7.10
`EntityVillager` / `MerchantRecipeList` trading behaviour.

| X1 | Port |
|---|---|
| `EntityRinnosuke extends EntityVillager` | `rinnosuke` (`RinnosukeEntity extends AbstractVillager`), egg 0x373737 / 0x2D2DE0 |
| `VillagerRinnosuke` trade handler | `RinnosukeEntity.rinnosukeTrades()` |
| `ModelRinnosuke` / `RenderRinnosuke` (RenderLiving) | `client/mob/RinnosukeModel`, `P17Renderers.Plain` (no boss plate) |

## Trades (VillagerRinnosuke)

22 power → spiritual strike talisman; 20 iron → mini hakkero; nether star → magic broom; 10 power → 9 point;
10 point → 9 power; redstone → 64 power; lapis (dye 4) → 64 point; gold ingot → ender pearl.

## 1.7.10 villager trading, kept

- First look at the offers: shuffle the eight, add one via `addToListWithCheck` (a listed recipe with the same
  items is replaced by a fresh copy, same ids otherwise kept).
- Each recipe has the default 7 uses. Trading the last listed recipe starts a 40-tick timer (paused while
  trading). When it runs out: if more than one recipe is listed, every used-up one gains 2–12 uses; one more
  random recipe is added; Regeneration I for 200 ticks.
- No trade XP, levels or job-site restock (1.20 features 1.7.10 did not have).
- Never breeds, despawns like a monster, cluster 1, lightning turns him into a witch.
- Spawns: ambient, weight 1, X1's 26 overworld base biomes, 2 % of attempts and not on uniform ground.

## Deviations

- Spawn group 0–1 → 1–1 (1.20 needs a positive minimum).
- AI is the 1.7.10 villager task list without village-only tasks (move indoors, mating, golem following, play).
- A 1.7.10 zombie also turned any `EntityVillager` (him included) into a zombie villager; 1.20 does that
  only for its own `Villager`, so that conversion is not reproduced.
- The trade screen title is his name (1.7.10 passed the custom name, usually none).

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_RINNOSUKE_PASS offers=2` (one of eight, 7 uses, reset adds one +
  regeneration, save / load, lightning → witch), P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; Rinnosuke inspected by eye in the P17 frame (not committed).

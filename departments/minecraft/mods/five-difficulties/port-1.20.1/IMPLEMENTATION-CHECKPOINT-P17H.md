# Implementation checkpoint — P17h Reimu and Miko

Date: 2026-11-20
Oracle: X1 `EntityReimu`, `EntityMiko`, `ModelReimu`, `ModelMiko`, `CommonProxy`.

| X1 | Port |
|---|---|
| `EntityReimu` | `reimu` (`ReimuEntity`); no spawn egg, no natural spawns (as X1) |
| `EntityMiko` | `miko` (`MikoEntity extends ReimuEntity`); no spawn egg, no natural spawns |
| `ModelReimu` / `ModelMiko` | `client/mob/ReimuModel`, `MikoModel` (generated trees, per-frame pivots) |
| `THKaguyaConfig.danmakuLevel =` | `X1Config.setDanmakuLevelInMemory` |

## X1 behaviour kept on purpose

- Reimu: 74 HP, 250 XP, speed 0.4, flying height 4, detection 0 (she fights whoever hits her). She starts in
  「夢想封印」 (card 0); that death is final. Her `isEntityInvulnerable` replaces the base one, so only
  `NOT_ATTACK` protects her and the between-phase `attackInterval` does not. Spell-card kills fan out 12
  power and 12 point items (yaw k·30 / +15°, pitch −60, speeds 0.5 / 0.3).
- Miko is Reimu's code with her name, saint species and flying height 0, starting in `NOT_ATTACK`, so she is
  invulnerable and never fights. Right-click on odd ticks cycles the danmaku level EASY → NORMAL → HARD →
  LUNATIC → EASY in memory (X1 writes the config field, not the file) and tells the player the new level.
- `getCanSpawnHere` is false for both: no natural or spawner spawns (1.7.10 spawners asked it too).
- Base `attackEntityFrom` returns true only for a living attacker; the damage still applies otherwise.

## Shared change

- `DanmakuMobEntity.isX1Invulnerable()` is the X1 `isEntityInvulnerable` hook (between phases by default);
  Reimu / Miko and the traders override it instead of `isInvulnerableTo`.
- Scratch model converter: picks the constructor that builds the parts and no longer swallows the next one.

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_REIMU_MIKO_PASS cycle=HARD`, P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; Reimu and Miko inspected by eye in the P17 frame (not committed).

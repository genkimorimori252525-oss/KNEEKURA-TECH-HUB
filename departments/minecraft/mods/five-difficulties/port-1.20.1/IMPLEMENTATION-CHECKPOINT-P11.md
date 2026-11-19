# Implementation checkpoint — P11 spell-card core and the first 30 cards

Date: 2026-11-19
Oracle: X1 `EntitySpellCard`, `THSpellCard` / `ITHSpellCard`, `SpellCardRegistry`, `ItemTHSpellCard`,
`EntitySpellCardCircle`, `EntityShotMaterial`, `THShotLib` (the parts the cards call), and the
`THSC_*` cards registered in `CommonProxy`.

## Ported

| X1 | Port |
|---|---|
| `THSpellCard` + `ITHSpellCard` | `forge/spellcard/X1SpellCard` (field names and helpers follow X1) |
| `SpellCardRegistry.registerSpellCard` | `X1SpellCardRegistry` (X1 names and IDs) |
| `ItemTHSpellCard.spellCardDeclaration` + its `onItemRightClick` check | `X1SpellCardDeclaration.check` / `declare` |
| `ItemTHSpellCard` (one item, damage = card ID) | `SpellCardItem`, one item per card, `spell_card_<name>` |
| `EntitySpellCard` | `forge/entity/SpellCardEntity` |
| `EntitySpellCardCircle` (+ render) | `SpellCardCircleEntity`, `SpellCardRenderers.Circle` |
| `EntityShotMaterial`, `ItemShotMaterial` | `ShotMaterialEntity`, `ShotMaterialItem` |
| `THShotLib` facade used by the cards | `forge/shot/X1Danmaku` |
| `THKaguyaCore.tabSpellCard`, sounds.json events | `PortRegistries.SPELL_CARD_TAB`, four sound events |

Registered cards (30 of the 35 X1 registers; the remaining five need their own entities, P12):

| ID | Card (X1 en / ja) | Shots fired in the scenario |
|---|---|---|
| 2 | Deadly Butterfly "Everlasting Nap" / 死蝶「華胥の永眠」 | 450 |
| 3 | Star Sign "Meteonic Shower" / 星符「メテオニックシャワー」 | 14 |
| 4 | Boundary Sign "Boundary between Wave and Particle" / 境符「波と粒の境界」 | 3300 |
| 5 | Sinister Spirits "Double Black Death Butterfly" / 魍魎「二重黒死蝶」 | 480 |
| 6 | Scarlet Sign "Scarlet Shoot" / 紅符「スカーレットシュート」 | 442 |
| 7 | "Sky of Scarlet Perception of All Humankind" / 「全人類の緋想天」 | 0 |
| 9 | Freeze Sign "Perfect Freeze" / 凍符「パーフェクトフリーズ」 | 333 |
| 11 | Water Sign "Kappa's Pororoca" / 水符「河童のポロロッカ」 | 154 |
| 12 | Magic Sign "Stardust Reverie" / 魔符「スターダストレヴァリエ」 | 7 |
| 13 | Native God "Kero-chan Braves the Wind and Rain" / 土着神「ケロちゃん風雨に負けず」 | 948 |
| 14 | Miracle "Miracle Fruit" / 奇跡「ミラクルフルーツ」 | 16 |
| 16 | Youkai Extermination "Bewitching Power Spoiler" / 妖怪退治「妖力スポイラー」 | 273 |
| 17 | Sea Opening "Moses's Miracle" / 開海「モーゼの奇跡」 | 1980 |
| 18 | Great Miracle "Yasaka's Divine Wind" / 大奇跡「八坂の神風」 | 2120 |
| 19 | Ice Sign "Icicle Fall" / 氷符「アイシクルフォール」 | 504 |
| 20 | Forbidden Barrage "Starbow Break" / 禁弾「スターボウブレイク」 | 336 |
| 21 | Forbidden Barrage "Catadioptric" / 禁弾「カタディオプトリック」 | 510 |
| 22 | Scourge Sign "Mishaguji-sama" / 祟符「ミシャグジさま」 | 640 |
| 23 | "Red Magic" / 「レッドマジック」 | 72 |
| 24 | Conjuring "Eternal Meek" / 奇術「エターナルミーク」 | 120 |
| 25 | Love Sign "Non-Directional Laser" / 恋符「ノンディレクショナルレーザー」 | 10 |
| 26 | Fantasy "The Beauty of Nature" / 幻想「花鳥風月、嘯風弄月」 | 630 |
| 27 | Divine Spear "Spear the Gungnir" / 神槍「スピア・ザ・グングニル」 | 0 |
| 28 | Moon Sign "Moonlight Ray" / 月符「ムーンライトレイ」 | 7 |
| 29 | Flower Sign "Gorgeous Sweet Flower" / 華符「芳華絢爛」 | 824 |
| 30 | Colorful Sign "Colorful Light Chaotic Dance" / 彩符「彩光乱舞」 | 710 |
| 33 | Hourai "South Wind, Clear Sky -Fujiyama Volcano-" / 蓬莱「凱風快晴 -フジヤマヴォルケイノ-」 | 7 |
| 34 | Wriggle Sign "Little Bug Storm" / 蟲符「リトルバグストーム」 | 300 |
| 35 | Firefly Sign "Meteor on Earth" / 蛍符「地上の流星」 | 14 |
| 40 | Thunder Arrow "Gagouji's Cyclone" / 雷矢「ガゴウジサイクロン」 | 554 |

The shot counts are what each card spawned in one run with a static target 6 blocks ahead
(lasers count as shots). Cards 7 and 27 fire nothing from `spellcard_main` in X1 either.

Not registered yet: 0 (Musou Fuuin), 1 (Master Spark), 8 (Satuzin Doll), 10 (Hikouchuu Nest),
15 (Fafrotskies) — each spawns an entity that is not ported yet.

## X1 behaviour kept on purpose

- Declaring costs `needLevel` experience levels (bombs first, once P14 adds them); creative users
  pay nothing. Cards 14–18 also need the item's `Charge` tag, which counts down every tick.
- The look ray for the target starts at the eyes but its far end is measured from the feet.
- A user with an active card (within 64 blocks) cannot declare another.
- Declaring with `firstAttack` removes *enemy* danmaku within 40 blocks of the user; while a player
  card is within its remove time it keeps removing other users' danmaku within 40 blocks.
- The card entity sits 30° to the user's right at eye height − 0.1; only player cards get a circle.
- A shot whose non-player user is dead turns into a shot material, which flies to the nearest
  player within 20 blocks (or vanishes) and becomes a Shot Material item on contact.

## Fix found on the way

1.20.1 `Projectile.getOwner()` returns null once the owner entity is removed, while 1.7.10 keeps the
(dead) `userEntity` reference. Shots of a user that is removed at once (no death animation) were
therefore discarded instead of leaving their bonus. `THShotEntity` now remembers the last user and
treats a removed non-player user as dead, which is what X1 sees.

## Receipts

Pure core: 10 suites PASS.

Dedicated server (local; P5/P6/P8/P9/P10/P11 together, all PASS):

```
FIVE_DIFFICULTIES_P11_COST_PASS levelsLeft=2
FIVE_DIFFICULTIES_P11_CARDS_PASS cards=30 shots=2:450 3:14 4:3300 ... 40:554
FIVE_DIFFICULTIES_P11_BONUS_PASS materials=2 afterTicks=1
FIVE_DIFFICULTIES_P11_RUNTIME_SCENARIO_PASS
```

- COST: Mishaguji-sama (need level 3) is refused at 2 levels, declared at 5 leaving 2, then refused
  while the first card is active.
- CARDS: all 30 cards declared at once, each by its own creative fake player at an invulnerable
  husk; every card ends within `endTime + 3` ticks, its circle is removed with it, and every card
  except 7 / 27 fires danmaku.
- BONUS: a dying husk and an armor stand that is removed at once both leave a shot material.

The P11 area is 70 blocks from spawn: declaring clears enemy danmaku within 40 blocks, which
otherwise removed the P10 lasers mid-test.

Real client (local, private overlay):

- `FIVE_DIFFICULTIES_P11_CLIENT_RESOURCES_PASS spellCards=30 laserItems=3`: every card item model
  resolves and its art and level frame exist; the laser items and the shot material too.
- In-world frame `p11_spellcard.png` (colourful delta 0.025): card 2 declared toward the camera —
  red magic circle, the card, butterfly danmaku and the declaration message in chat.

## Not covered

- Spell cards used by X1 danmaku mobs (`EntityDanmakuMob` spell card mode) arrive with the mobs (P17).
- Bombs (`bombItem`) are a supplier returning null until P14.
- `DanmakuPatternRegistry` is not ported: only the fairy / familiar / phantom mobs read it, so it
  moves to P17 with them.

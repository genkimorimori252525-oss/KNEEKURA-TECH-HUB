# Kimetsu ver3 — Combat Technique Opcode Map

Pinned binary:
`b4af6e8a9d5926c5fea212a5e237e61f1e8095a5be23eca9b8294258a3b466b6`

This map records the numeric namespaces used by the compiled Procedure dispatchers.

These numbers are **implementation protocol**, not user-facing lore IDs.

## Why this matters

Player and NPC combat code communicate through persistent numeric fields such as:

- `breathes`
- `mode`
- `demon_art`
- `skill`

Player selector procedures and NPC AI procedures then dispatch the same concrete form Procedure.

Example:

```text
PlayerBreathStoneProcedure
  breathes=1601 -> BreathesIwa1Procedure

AIHimejimaProcedure
  mode=1601 -> BreathesIwa1Procedure
```

This is a valuable reuse boundary: **who selected the technique** is separate from **how the
technique executes**.

## Breathing namespaces

| Style | Numeric opcode surface observed | Dispatcher |
|---|---|---|
| Thunder | 101–107, 111–113 | PlayerBreathThunder |
| Hinokami Kagura | 201–212 | PlayerBreathHinokamiKagura |
| Flame | 301–305, 309 | PlayerBreathFlame |
| Mist | 401,402,403,405,406,407 | PlayerBreathMist |
| Wind | 501–509 | PlayerBreathWind |
| Water | 601–611 | PlayerBreathWater |
| Beast | 701–705,707 | PlayerBreathBeast |
| Serpent | 801–805 | PlayerBreathSerpent |
| Insect | 901–904 | PlayerBreathInsect |
| Senior/custom | 1000,1001,1002,1004,1010,1011,1013,1014 | PlayerBreathSenior |
| Moon | 1101,1102,1103,1105–1110,1114,1116; swing 1120 | PlayerBreathMoon |
| Sun | 1201–1213 | PlayerBreathSun |
| Sound | 1301,1304,1305; swing 1320 | PlayerBreathSound |
| Flower | 1402,1404,1405,1406 | PlayerBreathFlower |
| Love | 1501,1502,1503,1505,1506 | PlayerBreathLove |
| Stone | **1601–1605** | PlayerBreathStone |
| Bamboo | 1701–1712 | PlayerBreathBamboo |
| Cherry Blossom | 1801–1806,1808–1810 | PlayerBreathCherryBlossom |

## Stone Breathing — ver3 addition

Public ver3 release notes say Stone Breathing was added.

Current binary dispatch:

- 1601 -> `BreathesIwa1Procedure`
- 1602 -> `BreathesIwa2Procedure`
- 1603 -> `BreathesIwa3Procedure`
- 1604 -> `BreathesIwa4Procedure`
- 1605 -> `BreathesIwa5Procedure`

Both:

- player dispatcher `PlayerBreathStoneProcedure`
- Himejima NPC AI `AIHimejimaProcedure`

call those same form implementations.

### Himejima selection

Static bytecode:

`AIHimejimaProcedure.execute`

Important offsets:

- ~100–247: active `mode` dispatch 1601..1605
- ~384–445: when attack timer expires, reset `cnt_x/cnt1/cnt2/cnt3`
- ~447: calculate target distance
- ~455–464: random integer 1601..1605
- ~467–506: distance/form comparisons
- ~511–527: write selected value to both `breathes` and `mode`
- ~532: `DirectionProcedure.execute`

### Current no-op distance filter

The bytecode around offsets 467–506 compares:

- distance >8 and selected form 1603
- close distance and forms 1602/1604

but every branch converges at offset 506 without modifying or rerolling the selected value.

**DIRECT_OBSERVATION:** the distance checks do not change current ver3 behavior.

**INFERENCE:** the code looks like an unfinished/generated attempt to filter forms by range.

Do not reconstruct the no-op as a required design rule.

## Blood Demon Art namespaces

Observed player demon-art selector bands:

| Art / character family | Opcode surface |
|---|---|
| Doma | 100–108 |
| Rui | 200–207 |
| Nezuko | 300 |
| Akaza | 400–409; swing 420/421 |
| Gyutaro / Daki | 500–502, 520, 550 |
| Muzan | 600,601,608,609,650,660 |
| Gyokko | 700–706,720,721 |
| Hantengu | 800–805,850,821,822 |
| Hand Demon | 900 |
| Yahaba | 1000,1001 |
| Kamanue | 1100–1104 |
| Enmu | 1200,1202 |
| Hairo | 1300,1301,1302,1308,1309,1320 |
| Rokuro | 1400–1403 |

## Player Blood Art selection pipeline

The R-key path is not direct skill execution.

```text
client key
    |
ChangeBreathesAndBloodArtMessage
    |
server ChangeArtProcedure
    |
player persistent ChangeArt=true
    |
held Blood Art item's inventory tick
    |
ChangingArtProcedure
    |
item NBT change_flag=true
    |
ChangeKekkizyutuProcedure
    |
cycle item NBT:
  select
  select_name
  select_cooltime
```

Evidence:

- `ChangingArtProcedure.execute`:
  - reads/writes `ChangeArt`
  - writes item `change_flag`
  - calls `ChangeKekkizyutuProcedure`
- many Blood Art items contain direct references to `ChangingArtProcedure`
  including Enmu, Gyokko, Kamanue, Muzan, Rokuro, Yahaba, Nezuko, Rui-related items and others.

This is a **selection-state protocol embedded in ItemStack NBT**.

## Representative demon FSM — Akaza

`AIakazaProcedure` uses persistent:

- `flag`
- `cnt_death`
- `mode`
- `cnt_target`
- `cnt_x`
- `cnt1`
- `cnt2`
- `cnt3`
- `demon_art`

Representative mode calls include:

- Ranshiki
- Kushiki
- Messhiki
- Manyou
- Shushiki
- Kishinyaeshin
- Ryusengunko
- Hiyuseisenrin
- Rashin

The architecture is a numeric imperative FSM layered over vanilla target/navigation Goals.

## Recommended KNEEKURA reconstruction

Keep:

```text
TechniqueId
TechniqueSelector
TechniqueExecutor
TechniqueRuntimeState
```

Avoid:

- magic-number doubles in persistent NBT
- style identity inferred from arithmetic ranges everywhere
- one global mutable NBT namespace shared by unrelated attacks

A typed representation could preserve the useful reuse:

```text
TechniqueId.STONE_FORM_1
  -> StoneForm1Executor

Player selector ─┐
NPC planner ─────┼─> same executor
Scripted event ──┘
```

without preserving the generated magic-number protocol.

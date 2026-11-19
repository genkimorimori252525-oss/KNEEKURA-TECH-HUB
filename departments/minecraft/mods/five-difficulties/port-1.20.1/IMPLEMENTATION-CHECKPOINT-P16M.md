# Implementation checkpoint — P16m third eye, bloodthirsty orb, Hourai branch

Date: 2026-11-20
Oracle: X1 `ItemThirdEye`, `ItemBloodthirstyOnmyoudama`, `ItemHouraiJeweledBranch`.

## Ported (`X1ToolItems`)

| X1 | Port |
|---|---|
| `ItemThirdEye` (第三の眼) | `third_eye` |
| `ItemBloodthirstyOnmyoudama` (血に餓えた陰陽玉) | `bloodthirsty_yin_yang_orb` |
| `ItemHouraiJeweledBranch` (蓬莱の玉の枝) | `hourai_jeweled_branch` (+ five charge icons through `charge_step`) |

## X1 behaviour kept on purpose

- The 64-block look trace measures the far end from the feet (X1 quirk), then picks the nearest living thing.
- Third eye: the read target lives on the item instance (shared by all holders and both sides of an
  integrated server, as in X1); the next inventory tick posts name, HP in hearts (rounded to 0.01) and a tame
  animal's owner. The port skips an offline owner, where X1 would throw.
- Bloodthirsty orb: release to jump 2 short of the target, feet `(int)(…) + 0.1`; 1 durability a use and,
  like 1.7.10, it breaks only when damage goes past 150. X1's conversion back to the yin-yang orb builds a stack
  it never returns, so it does nothing; not ported.
- Hourai branch: a sneak release fires `(32 + held, max 72) / 3` per ring, rings at i = 0, 3, … (speed 0.3 + 0.2 i,
  turned 3 i degrees) of rainbow pearls, while Charge ≤ 200; any release costs 50 Charge; 50 comes back every
  50 ticks of the holder. A plain release fires nothing: X1's forward volley is empty.

## Deferred

- `ItemMikoSword` (豊聡耳の剣) spawns `EntityDivineSpirit` and checks `EntityTHFairy`: with P17 / P18.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_THIRD_EYE_PASS
FIVE_DIFFICULTIES_P16_BLOODTHIRSTY_ORB_PASS dx=8.01
FIVE_DIFFICULTIES_P16_HOURAI_BRANCH_PASS shots=70
```

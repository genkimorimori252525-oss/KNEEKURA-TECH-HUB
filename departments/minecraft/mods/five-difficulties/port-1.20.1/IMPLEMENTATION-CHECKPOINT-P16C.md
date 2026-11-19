# Implementation checkpoint — P16c danmaku items without their own entity

Date: 2026-11-20
Oracle: X1 `ItemSoulTorch`, `ItemYuyukoFan`, `ItemKappaWaterPistol`, `ItemIbukihyou`.

## Ported (`X1ShotItems`)

| X1 | Port |
|---|---|
| `ItemSoulTorch` (人魂灯, special 352) | `soul_torch` |
| `ItemYuyukoFan` (桜花扇) | `yuyuko_fan` |
| `ItemKappaWaterPistol` | `kappa_water_pistol` |
| `ItemIbukihyou` (伊吹瓢) | `ibuki_gourd` |

## X1 behaviour kept on purpose

- Soul torch: stack 16, 12-tick use; three purple phantoms (size 0.4, damage 7, end 480) in a ring straight up,
  special 352 = homing 16 and not stopped by blocks (registered from the item's constructor, as X1). A creative
  click fires at once and the finished use fires again.
- Yuyuko fan: 32 + held ticks butterflies, capped at 72, rounded down to threes; ahead two mirrored fans of
  (n/3 + 1), sneak six counter-turning rings of n/3; 5% instant kill (4444) of a wounded target under 20 that
  heals the user; durability 444, glint.
- Water pistol: three falling blue light shots (gravity −0.03) per click, 40° to the right; the 39th charge
  (damage 38) never fires; sneak at a water source refills 2.
- Ibuki gourd: drink only while damage < 6, each drink costs 5 (two drinks), Strength 15 s and Nausea III 20 s;
  sneaking when the drink finishes keeps it untouched; a water source refills 1 per click.
- `THShotEntity.homing` is now public so special shots can call it, as X1's `shot.homing(level)`.

## Receipts

Dedicated server (local; P5–P16 together):

```
FIVE_DIFFICULTIES_P16_SOUL_TORCH_PASS shots=3
FIVE_DIFFICULTIES_P16_YUYUKO_FAN_PASS wide=30 rings=84
FIVE_DIFFICULTIES_P16_WATER_PISTOL_PASS
FIVE_DIFFICULTIES_P16_IBUKI_GOURD_PASS
FIVE_DIFFICULTIES_P16C_SHOT_ITEMS_PASS
```

## Known flake (not caused by P16)

P9's HOMING01 check sometimes fails ("did not bend toward the target"). Measured: with the P16 scenario off it
failed 1 run of 2, with it on it passed 2 of 3 runs. When it passes the homing minimum is always 0.769; failing
runs show 4.6–6.0, as if the shot chose another target. Hypothesis (unmeasured): a mob from another scenario
is inside the 24-block homing search at that tick. To be investigated separately.

## Not covered

- In-world client frames; TechHub Tank gameplay checks (the Tank currently proves boot and clean exit only).

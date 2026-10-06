# Warfare Wings Aircraft Atlas — 24 Base Aircraft (v2)

> Status: **SOURCE MICROKERNEL ONLY / SAME-ARTIFACT MINECRAFT CALIBRATION PENDING.**
> Same-input and equal-angle turn metrics are intentionally separate. No composite “best aircraft” score is calculated.

## Global extrema

| Axis | Best / highest-priority end | Value | Opposite end | Value | Rank direction | Evidence |
|---|---|---:|---|---:|---|---|
| Source-predicted speed | `warfare_wings:p47n` | 45.791246 | `warfare_wings:b17` | 20.202020 | `higher_value_first` | `SOURCE_MICROKERNEL` |
| Yaw response / 20t | `warfare_wings:il2` | 36.039128 | `warfare_wings:b17` | 10.811738 | `higher_value_first` | `SOURCE_MICROKERNEL` |
| Pitch response / 20t | `warfare_wings:a6m` | 31.534237 | `warfare_wings:b17` | 9.910760 | `higher_value_first` | `SOURCE_MICROKERNEL` |
| 20t same-input speed retention | `warfare_wings:b17` | 0.998560 | `warfare_wings:a6m` | 0.976949 | `higher_value_first` | `SOURCE_MICROKERNEL_IDENTICAL_INPUT` |
| Ticks to 90° yaw | `warfare_wings:il2` | 41 | `warfare_wings:b17` | 118 | `lower_value_first` | `SOURCE_MICROKERNEL_EQUAL_ANGLE` |
| 90° equal-angle speed retention | `warfare_wings:b17` | 0.994638 | `warfare_wings:a6m` | 0.925567 | `higher_value_first` | `SOURCE_MICROKERNEL_EQUAL_ANGLE` |
| Distance travelled to 90° yaw | `warfare_wings:il2` | 63.074088 | `warfare_wings:p47n` | 134.908910 | `lower_value_first` | `SOURCE_MICROKERNEL_EQUAL_ANGLE` |
| Durability | `warfare_wings:b29` | 6.50 | `warfare_wings:a6m` | 2.50 | `higher_value_first` | `SOURCE_DIRECT` |

## Why the two retention axes differ

- `same_input_retention`: speed retained after every aircraft receives the same full-yaw input for 20 ticks.
- `equal_angle_retention`: speed retained when each aircraft has actually changed yaw by 90°.
- A slow-turning aircraft can score high on both retention metrics, but `turn_90_ticks` and `distance_90` expose the time/space cost of achieving that turn.

### Representative equal-angle results

| Aircraft | 90° ticks | 90° retention | Distance to 90° | 20t yaw |
|---|---:|---:|---:|---:|
| `warfare_wings:il2` | 41 | 0.951955 | 63.074 | 36.039° |
| `warfare_wings:a6m` | 42 | 0.925567 | 68.547 | 34.237° |
| `warfare_wings:spitfire` | 44 | 0.935021 | 91.231 | 32.435° |
| `warfare_wings:yak3` | 46 | 0.939018 | 96.495 | 30.633° |
| `warfare_wings:ki84` | 48 | 0.941936 | 104.950 | 29.732° |
| `warfare_wings:p47n` | 60 | 0.964626 | 134.909 | 22.524° |
| `warfare_wings:b17` | 118 | 0.994638 | 118.738 | 10.812° |

## Doctrine contrasts

These are within-label ranges, not claims that the doctrine label itself caused the difference.

| Doctrine | N | 90° turn time | Equal-angle retention | Speed | Durability |
|---|---:|---|---|---|---|
| `turn_fighter` | 3 | `warfare_wings:a6m` 42 ↔ `warfare_wings:yak3` 46 | `warfare_wings:yak3` 0.939018 ↔ `warfare_wings:a6m` 0.925567 | `warfare_wings:yak3` 43.097643 ↔ `warfare_wings:a6m` 33.670034 | `warfare_wings:spitfire` 3.00 ↔ `warfare_wings:a6m` 2.50 |
| `energy_fighter` | 11 | `warfare_wings:ki84` 48 ↔ `warfare_wings:p47n` 60 | `warfare_wings:p47n` 0.964626 ↔ `warfare_wings:bf109` 0.941875 | `warfare_wings:p47n` 45.791246 ↔ `warfare_wings:p40e` 38.159371 | `warfare_wings:p47n` 5.00 ↔ `warfare_wings:mig3` 3.00 |
| `attacker` | 4 | `warfare_wings:il2` 41 ↔ `warfare_wings:ju87` 81 | `warfare_wings:ju87` 0.983141 ↔ `warfare_wings:il2` 0.951955 | `warfare_wings:d4y` 38.159371 ↔ `warfare_wings:ju87` 22.446689 | `warfare_wings:il2` 5.00 ↔ `warfare_wings:d4y` 3.30 |
| `escort` | 6 | `warfare_wings:g4m` 53 ↔ `warfare_wings:b17` 118 | `warfare_wings:b17` 0.994638 ↔ `warfare_wings:g4m` 0.968120 | `warfare_wings:g4m` 29.180696 ↔ `warfare_wings:b17` 20.202020 | `warfare_wings:b29` 6.50 ↔ `warfare_wings:he111` 4.00 |

## High-value contrasts for AI design

- **A6M:** 90° in 42 ticks, fastest of the three `turn_fighter` aircraft, but it also has the lowest equal-angle retention of all 24 (0.925567). Its advantage is rapid nose change, not low-cost turning.
- **Spitfire / Yak-3:** 44 / 46 ticks to 90° with 0.935021 / 0.939018 retention. They trade a little nose speed for less speed loss than A6M.
- **P-47N:** 60 ticks to 90° and 0.964626 retention while remaining the fastest source-speed aircraft. Inside `energy_fighter` it is slowest to rotate to 90° but best at equal-angle speed retention.
- **Ki-84:** 48 ticks to 90° versus P-47N's 60, but 0.941936 retention. This quantitatively separates a tighter energy fighter from a more extension-oriented one.
- **IL-2:** fastest 90° yaw result across all 24 at 41 ticks, reinforcing that attacker role does not imply low nose authority.
- **Ju 87:** 81 ticks to 90° with 0.983141 retention. Compared with IL-2, the same attacker label spans a very different control/time envelope.
- **B-17:** takes 118 ticks to reach 90° but still retains 0.994638 speed. Equal-angle normalization confirms low speed loss, while turn time shows the major tactical cost.
- **G4M:** reaches 90° in 53 ticks, far faster than B-17/B-29/G10N/He111 members of the `escort` group, so that label is not a single maneuver profile.
- **G10N1 vs G10N2:** remain identical in this wind-off Atlas despite mass 22 vs 17, consistent with mass not acting as ordinary yaw/pitch inertia in the inspected IA 1.3.3 path.

## Statistical inspection flags

Global 1.5×IQR flag count across the eight Atlas axes: **2**.

Within-doctrine flags (groups with at least 4 aircraft):
- `energy_fighter` / `distance_90`: `warfare_wings:p47n` = 134.908910197 (`STATISTICAL_IQR_FLAG`).
- `escort` / `same_input_retention`: `warfare_wings:g4m` = 0.990100052 (`STATISTICAL_IQR_FLAG`).
- `escort` / `equal_angle_retention`: `warfare_wings:g4m` = 0.968119706 (`STATISTICAL_IQR_FLAG`).

The 3-aircraft `turn_fighter` group is not IQR-tested because the sample is too small.

## Query flags

Query flags use global top/bottom quartile membership (6 of 24 aircraft per quartile). They are routing hints, not overall combat rankings.

- `HIGH_YAW_LOW_SAME_INPUT_RETENTION` / `HIGH_SAME_INPUT_RETENTION_LOW_YAW`: fixed-duration contrast.
- `FAST_90_LOW_EQUAL_ANGLE_RETENTION`: fast 90° completion paired with bottom-quartile equal-angle retention.
- `SLOW_90_HIGH_EQUAL_ANGLE_RETENTION`: slow 90° completion paired with top-quartile equal-angle retention.

## Interpretation boundary

The equal-angle metrics repair an important comparison problem, but they are still source-microkernel results. Same-artifact Minecraft trace calibration remains the promotion gate before any axis is labeled `MEASURED`.
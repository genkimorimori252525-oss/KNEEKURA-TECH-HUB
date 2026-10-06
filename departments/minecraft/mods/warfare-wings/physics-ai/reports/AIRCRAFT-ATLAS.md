# Warfare Wings Aircraft Atlas — 24 Base Aircraft

> Status: **SOURCE MICROKERNEL ONLY / SAME-ARTIFACT MINECRAFT CALIBRATION PENDING.**
> No composite “best aircraft” score is calculated.

## Global extrema

| Axis | Highest | Value | Lowest | Value | Evidence |
|---|---|---:|---|---:|---|
| Source-predicted speed | `warfare_wings:p47n` | 45.791246 | `warfare_wings:b17` | 20.202020 | `SOURCE_MICROKERNEL` |
| Yaw response / 20t | `warfare_wings:il2` | 36.039128 | `warfare_wings:b17` | 10.811738 | `SOURCE_MICROKERNEL` |
| Pitch response / 20t | `warfare_wings:a6m` | 31.534237 | `warfare_wings:b17` | 9.910760 | `SOURCE_MICROKERNEL` |
| 20t identical-input speed retention | `warfare_wings:b17` | 0.998560 | `warfare_wings:a6m` | 0.976949 | `SOURCE_MICROKERNEL_IDENTICAL_INPUT` |
| Durability | `warfare_wings:b29` | 6.50 | `warfare_wings:a6m` | 2.50 | `SOURCE_DIRECT` |

## Top-five lookup

- **Source-predicted speed:** 1. `warfare_wings:p47n` (45.791246), 2. `warfare_wings:f4u` (44.893378), 3. `warfare_wings:fw190` (44.893378), 4. `warfare_wings:ki84` (44.893378), 5. `warfare_wings:p51d` (44.893378)
- **Yaw response / 20t:** 1. `warfare_wings:il2` (36.039128), 2. `warfare_wings:a6m` (34.237171), 3. `warfare_wings:spitfire` (32.435215), 4. `warfare_wings:yak3` (30.633258), 5. `warfare_wings:ki84` (29.732280)
- **Pitch response / 20t:** 1. `warfare_wings:a6m` (31.534237), 2. `warfare_wings:il2` (31.534237), 3. `warfare_wings:spitfire` (30.633258), 4. `warfare_wings:yak3` (29.732280), 5. `warfare_wings:ki84` (27.930324)
- **20t identical-input speed retention:** 1. `warfare_wings:b17` (0.998560), 2. `warfare_wings:b29` (0.998420), 3. `warfare_wings:g10n1` (0.996385), 4. `warfare_wings:g10n2` (0.996385), 5. `warfare_wings:ju87` (0.995772)
- **Durability:** 1. `warfare_wings:b29` (6.500000), 2. `warfare_wings:b17` (6.000000), 3. `warfare_wings:g10n1` (5.500000), 4. `warfare_wings:g10n2` (5.500000), 5. `warfare_wings:il2` (5.000000)

## Doctrine contrasts

These are within-label ranges, not claims that the doctrine label itself caused the difference.

| Doctrine | N | Speed range | Yaw range | Retention range | Durability range |
|---|---:|---|---|---|---|
| `turn_fighter` | 3 | `warfare_wings:a6m` 33.670 → `warfare_wings:yak3` 43.098 | `warfare_wings:yak3` 30.633 → `warfare_wings:a6m` 34.237 | `warfare_wings:a6m` 0.976949 → `warfare_wings:yak3` 0.982125 | `warfare_wings:a6m` 2.50 → `warfare_wings:spitfire` 3.00 |
| `energy_fighter` | 11 | `warfare_wings:p40e` 38.159 → `warfare_wings:p47n` 45.791 | `warfare_wings:p47n` 22.524 → `warfare_wings:ki84` 29.732 | `warfare_wings:ki84` 0.983363 → `warfare_wings:p47n` 0.990869 | `warfare_wings:mig3` 3.00 → `warfare_wings:p47n` 5.00 |
| `attacker` | 4 | `warfare_wings:ju87` 22.447 → `warfare_wings:d4y` 38.159 | `warfare_wings:ju87` 16.218 → `warfare_wings:il2` 36.039 | `warfare_wings:il2` 0.981860 → `warfare_wings:ju87` 0.995772 | `warfare_wings:d4y` 3.30 → `warfare_wings:il2` 5.00 |
| `escort` | 6 | `warfare_wings:b17` 20.202 → `warfare_wings:g4m` 29.181 | `warfare_wings:b17` 10.812 → `warfare_wings:g4m` 26.128 | `warfare_wings:g4m` 0.990100 → `warfare_wings:b17` 0.998560 | `warfare_wings:he111` 4.00 → `warfare_wings:b29` 6.50 |

## High-value contrasts for AI design

- **P-47N:** globally fastest source tendency (45.791 b/s), but lowest yaw and pitch response inside `energy_fighter`; it also has that doctrine's highest identical-input retention. This supports a larger extension/re-entry envelope rather than copying a tighter energy-fighter policy.
- **Ki-84:** tied near the top of source speed (44.893 b/s) while leading `energy_fighter` yaw/pitch response; its 20-tick identical-input retention is the lowest in that doctrine. A single P-47-style policy would erase this difference.
- **A6M / Spitfire / Yak-3:** all are `turn_fighter`, but A6M has the highest yaw/pitch response and much lower source speed, while Yak-3 has the highest source speed of the three. The label is not a full flight profile.
- **IL-2:** has the highest yaw response of all 24 aircraft despite being an attacker. Historical role stereotypes must not override runtime control values.
- **Ju 87 vs IL-2:** both are `attacker`, yet Ju 87 is the slowest/lowest-yaw attacker while IL-2 is the highest-yaw/highest-durability attacker. Mission-specific attack logic needs aircraft parameters, not only the shared doctrine string.
- **G4M:** is the fastest and highest-yaw member of the `escort` group. Its retention is the only within-doctrine 1.5×IQR statistical flag in the five Atlas axes; this is an inspection hint, not a physics anomaly.
- **G10N1 vs G10N2:** they have identical source-microkernel Atlas features even though raw mass differs (22 vs 17). In this wind-off baseline that is expected: mass is not ordinary yaw/pitch inertia in the inspected IA 1.3.3 path.
- **B-17/B-29:** very high 20-tick retention accompanies very low achieved yaw/pitch. That metric is therefore not “turning efficiency”; it is speed retained under the same control input and must later be complemented by an equal-angle turn test.

## Statistical inspection flags

Global 1.5×IQR flag count across the five Atlas axes: **0**.

Within-doctrine flags (groups with at least 4 aircraft):
- `escort` / `retention`: `warfare_wings:g4m` = 0.990100052 (`STATISTICAL_IQR_FLAG`).

The 3-aircraft `turn_fighter` group is not IQR-tested because the sample is too small.

## Query flags

Query flags use global top/bottom quartile membership (6 of 24 aircraft per quartile). They are routing hints, not rankings of overall combat strength.

- `HIGH_YAW_LOW_RETENTION`: top-quartile yaw response + bottom-quartile identical-input retention.
- `HIGH_RETENTION_LOW_YAW`: top-quartile identical-input retention + bottom-quartile yaw response.
- `HIGH_SPEED_LOW_YAW` / `LOW_SPEED_HIGH_YAW`: reserved for the corresponding speed/yaw quartile contrasts; none are present in this Atlas revision.

## Interpretation boundary

The Atlas is deliberately source-faithful and explainable, but it is **not yet measured same-artifact performance**. The first real-runtime calibration remains A6M `a6m-throttle-step-v1`. Once that trace arrives, the same calibration method will determine which Atlas axes can be promoted from `SOURCE_MICROKERNEL` toward `MEASURED` for the supplied Warfare Wings artifact.
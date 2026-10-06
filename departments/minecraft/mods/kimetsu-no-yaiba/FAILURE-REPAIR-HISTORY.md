# Kimetsu no Yaiba ver3 — Bounded Failure / Repair History

## Evidence model

Official source/commit history was not found.

History is therefore bounded to:

- public CurseForge 1.20.1 release notes
- current ver3 JAR bytecode
- current public project description

Do not infer the exact code change behind a release-note fix unless a historical binary diff is
performed.

## 1. ver1 — 1.20.1 port and performance claim

File:
`KimetsunoYaiba-ver1-forge-1.20.1.jar`

Uploaded:
2024-10-20

AUTHOR_CLAIM:
- compatible with Minecraft 1.20.1
- "Optimized the mod's performance to be lightweight"

Current ver3 static architecture still contains substantial generated-code/per-entity work, so the
historical claim is not treated as a current measured benchmark.

No ver1/ver3 runtime A/B was performed.

## 2. ver1.2 — infinite technique use fix

File:
`KimetsunoYaiba-ver1.2-forge-1.20.1.jar`

Uploaded:
2024-10-26

AUTHOR_CLAIM:
- fixed a bug where characters could use one Breath/Art infinitely under certain conditions

Current ver3 still uses:

- numeric `mode`
- `cnt_x/cnt1/cnt2/cnt3`
- technique reset/selection logic

It is plausible that the historical repair involved this action-state lifecycle, but the exact
mechanism is **UNKNOWN** without comparing the old binary.

Lesson:
every scripted attack needs an explicit:

```text
enter
active
terminate
reset
next-select
```

contract.

## 3. ver1.3 — generic bug-fix release

Uploaded:
2025-01-06

AUTHOR_CLAIM:
- fixed bugs

No issue list/source diff was pinned.

Status:
**UNRESOLVED_HISTORY**.

## 4. ver2 — animation subsystem introduction

File:
`KimetsunoYaiba-ver2-forge-1.20.1.jar`

Uploaded:
2025-08-28

AUTHOR_CLAIM:
- added animations for entities and players
- implemented bug fixes/improvements

Current ver3 contains two distinct animation systems:

- GeckoLib entity animation
- PlayerAnimator player animation

and 112 player-animation JSON assets.

Therefore animation is known to be a ver2+ architectural layer.

The exact ver2->ver3 binary changes were not diffed.

## 5. ver3 — Stone Breathing

File:
`KimetsunoYaiba-ver3-forge-1.20.1.jar`

Uploaded:
2025-10-26

AUTHOR_CLAIM:
- added Stone Breathing
- some improvements

Current JAR contains direct implementation evidence:

- `PlayerBreathStoneProcedure`
- `AIHimejimaProcedure`
- `BreathesIwa1..5Procedure`
- Himejima weapon helper entity / animation assets
- opcode band 1601..1605

This is a strong release-note-to-binary match.

## 6. Stone selection distance branch anomaly

Current ver3:
`AIHimejimaProcedure.execute`

After selecting random 1601..1605, bytecode compares distance/form values but all branches converge
without changing selection.

DIRECT_OBSERVATION:
distance check is functionally no-op.

INFERENCE:
likely generated/uncompleted selection filtering.

No runtime repair attempted.

## 7. Metadata dependency mismatch

Current public project page:
PlayerAnimator + GeckoLib required for 1.20.1.

Current JAR:
- hard bytecode references both APIs
- `mods.toml` marks dependency entries non-mandatory

Risk:
an absent library can fail at class loading/use time instead of being rejected cleanly by Forge
dependency resolution.

This is an active compatibility boundary rather than a known repaired bug.

## 8. Animation signaling through DamageSource

Current ver3:

`PlayAnimationProcedure` inflicts 1 point with `kimetsunoyaiba:start_animation`.

`PlayAnimationPlayerProcedure` catches the corresponding LivingAttackEvent and sends animation
messages.

This can interact with any mod listening to/canceling/modifying damage events.

Status:
**CURRENT_DESIGN_RISK**.

Recommended reconstruction:
custom animation event/packet, not fake damage.

## 9. Worldgen internal-field mutation

Current ver3 uses Access Transformer and runtime mutation of ChunkGenerator /
NoiseBasedChunkGenerator internals.

Status:
**CURRENT_COMPATIBILITY_RISK**.

Potential conflicts:
- biome source replacement mods
- generator wrappers
- surface-rule mods
- worldgen optimizers

No incompatibility issue is asserted without runtime evidence.

## 10. Attack scratch-state leakage

Hundreds of Procedures communicate with persistent NBT keys such as:

`Damage`, `Range`, `knockback`, `projectile_type`, `cnt1`, `cnt2`, `cnt3`.

This architecture requires every attack path to overwrite the values it relies on.

A missing write can inherit state from a previous technique.

No specific reproduced leakage bug is claimed.

Status:
**STRUCTURAL_RISK**.

## 11. Explicit target matrices

Current compiled entities have ~1,521 anonymous target-goal classes.

This is not a known bug, but creates a repair burden:

- adding a new faction class may require updating many entities
- tags already exist but are not the main targeting abstraction

Status:
**MAINTAINABILITY / POSSIBLE PERFORMANCE RISK**.

## 12. Runtime verification gap

Not performed in this pass:

- TPS profiling
- FPS profiling
- memory/classloading profile
- helper-entity count under boss battles
- worldgen mod compatibility matrix
- missing GeckoLib/PlayerAnimator startup behavior
- multiplayer animation/state synchronization test

Static claims remain clearly separated from runtime claims.

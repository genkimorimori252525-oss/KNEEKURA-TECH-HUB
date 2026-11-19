# BWR-0016 — official persistence was lost through Monster inheritance

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (local GameTests)

## Symptom and root cause

Pinned Mojang wither.json (46ba6ea985fb5a92d79a9419198f10dda14c199d, format1.26.50) declares minecraft:persistent. The independent Java entity supplied no corresponding persistence override and inherited natural distance/random despawning from Monster/Mob.

Basis: official JSON, direct entity inspection and mapped Mob.checkDespawn/readAdditionalSaveData bytecode. A constructor-only ordinary persistence flag would not be sufficient because legacy NBT can overwrite that flag with false.

## Repair and regression

Use Mob's species-level custom-persistence hook, preserving its earlier Peaceful-removal branch. Exercise the actual despawn check with a registered eligible player beyond the despawn range on both new and real-NBT-restored legacy-false bosses. This repairs an existing official contract, not a newly invented Bedrock mechanic.

[Final source-bound verification](../../evidence/source-completion-2026-10-03.json)

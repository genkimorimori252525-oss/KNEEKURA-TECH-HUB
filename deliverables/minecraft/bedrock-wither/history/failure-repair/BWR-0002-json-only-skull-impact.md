# BWR-0002 — JSON-only inference removed Bedrock skull impact damage

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: REPAIR_IN_PROGRESS  
Environment: Minecraft Java 1.20.1 / Forge 47.2.0 reconstruction; Bedrock evidence pinned separately

## Symptom

The custom `BedrockWitherSkullEntity` deliberately overrode entity impact so a direct hit dealt **zero direct damage**, while applying only Wither II and the power-1 explosion.

A GameTest explicitly locked that behavior.

## Why it happened

The current Mojang behavior-pack definitions for:
- `minecraft:wither_skull`
- `minecraft:wither_skull_dangerous`

do not expose an `impact_damage` field.

The implementation incorrectly promoted that absence into a runtime claim:

> no exposed impact_damage => no direct impact damage.

That inference was invalid for an entity with runtime-identifier/native behavior.

## New evidence

### Historical Bedrock native body

Historical `WitherSkull::onHit` contains Wither-skull-specific native handling around:
- hit entity processing;
- owner/killer relationship;
- owner healing by 5 when the hit kills the target;
- Wither II effect by difficulty;
- explosion processing.

This proves the Bedrock skull path was not JSON-only.

### Current gameplay evidence

Current Minecraft/Bedrock documentation reports Wither Skull impact damage by difficulty:
- Easy: 5
- Normal: 8
- Hard: 12

with a separate skull explosion entry.

### Java ANCHOR comparison

Java 1.20.1 `WitherSkull.onHitEntity` uses a base-8 Wither-skull damage path when owned by a LivingEntity, retains owner heal-on-kill behavior and applies the same Normal/Hard Wither II durations.

The game's difficulty scaling produces the observed 5/8/12 damage contract.

## Root cause

Basis: INFERENCE ERROR confirmed by historical native code + current runtime documentation.

The evidence ladder was applied incorrectly. Official JSON remains the highest-value **exposed component** source, but it is not a complete description of hardcoded runtime identifiers or unique entity behavior.

## Repair

- restore the Java WitherSkull owned-entity hit path via `super.onHitEntity(...)`;
- keep KNEEKURA ownership of Bedrock-specific differences:
  - normal/dangerous launch power;
  - inertia;
  - dangerous reflection gate;
  - dangerous explosion-resistance adaptation;
  - explicit explosion lifecycle;
- replace the zero-impact GameTest with a 5/8/12 difficulty-aware impact test.

Repair commits:
- `4ad356d83ec8788bc592eb9e2742ca91e23025fe`
- `2cc2a975686dfb312beab0217dba36c1e77e12d3`

## Verification

Pending the dedicated Forge build + GameTest generation containing the repair.

## Reusable lesson

**Absence from Bedrock behavior JSON is not proof of absence at runtime.**

For runtime identifiers and unique entities:
1. inspect public JSON;
2. inspect current native structure;
3. inspect version-labelled historical native bodies where useful;
4. cross-check current runtime observation;
5. only then decide whether Java behavior is leakage or a useful matching primitive.

This case is a concrete example for the reusable native-overrides-public-component technique.

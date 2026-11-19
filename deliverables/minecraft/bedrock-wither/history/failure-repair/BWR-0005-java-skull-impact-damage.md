# BWR-0005 — Java WitherSkull superclass did not match Bedrock impact damage

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: VERIFIED_FIXED

## Symptom

Forge GameTest run `36991331495` failed:

`entityhitmatchesbedrockimpactdamage failed! Bedrock skull impact damage expected 5.0 on EASY but was 8.0`

## Root cause

Basis: DIRECT_OBSERVATION + source comparison.

After correcting the earlier JSON-only mistake, KNEEKURA reused Java 1.20.1 `WitherSkull.onHitEntity` via `super`.

Java's owned-skull path applies a fixed direct-hit damage value of 8 before Wither effect handling. It does **not** implement Bedrock's current difficulty-dependent 5 / 8 / 12 impact damage.

The reuse was directionally useful for:
- owner attribution;
- owner heal-on-kill = 5;
- Wither II duration on Normal/Hard;

but too broad for direct damage.

## Bedrock evidence

Current gameplay documentation reports skull impact damage:
- Easy: 5
- Normal: 8
- Hard: 12

Historical Bedrock native `WitherSkull::onHit` independently proves that the skull has native direct-hit logic, owner kill-heal behavior, Wither effect logic and explosion processing beyond public projectile JSON.

## Repair plan

Own the entity-hit path in `BedrockWitherSkullEntity`:
- apply explicit Bedrock difficulty damage;
- preserve owner attribution;
- preserve owner heal-on-kill = 5;
- preserve Wither II durations: Normal 200 ticks / Hard 800 ticks;
- keep explosion handling independent in `onHit`.

Do not call Java `WitherSkull.onHitEntity`.

## Verification

Dedicated Forge workflow run `36993986762` (source `c230bd372ca2ee96bc0396e424071d2f4c06cb3a`) completed successfully. The GameTest server ran 14 required tests in isolated batches and reported `All 14 required tests passed :)`.

The isolated `entityHitMatchesBedrockImpactDamage` batch passed with the explicit Bedrock impact mapping and Wither-effect contract. The product no longer calls Java `WitherSkull.onHitEntity` as a whole-method semantic substitute.

Workflow: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36993986762

## Lesson

Superclass reuse is acceptable only at a verified semantic boundary. Matching some behavior is not evidence that the entire Java method matches Bedrock.

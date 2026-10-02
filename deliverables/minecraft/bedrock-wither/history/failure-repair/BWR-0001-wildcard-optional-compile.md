# BWR-0001 — wildcard Optional compile failure

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: REPAIR_IN_PROGRESS  
Environment: Minecraft 1.20.1 / Forge 47.2.0 / Java 17 / GitHub Actions Gradle 8.1.1

## Symptom

Forge `compileJava` failed for product source generation `9c6eb33069d467e36f6a4ed06ef5d4a7649e18fc`.

Workflow evidence:
- run: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36978390934
- job: `110747152164`
- task: `:compileJava`

Compiler diagnostic:

`Optional<CAP#1> cannot be converted to Optional<LivingEntity>`

at `BedrockWitherThreatLedger.selectHighestDamageTarget(...).max(comparator)`.

## Trigger

The method accepted `Collection<? extends LivingEntity>` while declaring return type `Optional<LivingEntity>`. Java Stream preserved the wildcard capture through `max`, producing `Optional<? extends LivingEntity>`.

## Root cause

Basis: DIRECT_OBSERVATION from compiler type diagnostic plus source inspection.

The API intentionally accepts subtype collections, but the return conversion was omitted. This is a Java generic-capture issue, not a Forge/Minecraft API incompatibility.

## Repair

Convert the selected wildcard value to the declared base type after `max`, preserving the subtype-friendly input API:

```java
.max(comparator)
.map(LivingEntity.class::cast);
```

## Verification

Pending a clean build of the repaired exact source generation.

## Lesson

When a public selector accepts `Collection<? extends Base>` but promises `Optional<Base>`, make the widening conversion explicit at the return boundary. Do not narrow the input type merely to silence wildcard capture; callers should remain free to supply subtype collections.

# BWR-0003 — difficulty-health helper rename compile failure

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: REPAIR_IN_PROGRESS  
Environment: Minecraft 1.20.1 / Forge 47.2.0 / Java 17 / GitHub Actions Gradle 8.1.1

## Symptom

Dedicated Forge build failed at source generation `f9b99d2aabca42dcbf12330c3a33e2cafdd59640`.

Workflow:
- run: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36988829441
- job: `110780451197`

Compiler diagnostic:

```
BedrockWitherEntity.java:175: error: cannot find symbol
    applyBedrockDifficultyHealth();
    ^
symbol: method applyBedrockDifficultyHealth()
```

## Root cause

Basis: DIRECT_OBSERVATION from compiler output and source inspection.

A semantic rename changed the call site from `applyCandidateDifficultyHealth()` to `applyBedrockDifficultyHealth()`, but the method declaration retained the old name.

This is a local refactor consistency failure, not a Bedrock/Forge API issue.

## Repair

Rename the method declaration only. No gameplay behavior or evidence interpretation changes.

## Verification

Pending dedicated Forge build + GameTest on the repaired exact source generation.

## Lesson

When promoting a behavior from candidate/provisional wording to accepted runtime wording, treat method-name changes as mechanical refactors and verify all call/declaration references in the same commit. Evidence-status renaming must not create code drift.

# BWR-0003 — difficulty-health method rename broke compile

Date: 2026-10-02  
Origin: OWN_DEVELOPMENT  
State: REPAIR_IN_PROGRESS  
Environment: Minecraft 1.20.1 / Forge 47.2.0 / Java 17 / GitHub Actions Gradle 8.1.1

## Symptom

Dedicated Forge build failed at source generation `f9b99d2aabca42dcbf12330c3a33e2cafdd59640`.

Workflow:
- run: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36988829441
- job: `110780451197`
- task: `:compileJava`

Compiler diagnostic:

`cannot find symbol: method applyBedrockDifficultyHealth()`

in `BedrockWitherEntity.customServerAiStep()`.

## Root cause

Basis: DIRECT_OBSERVATION from compiler output + exact source inspection.

A refactor renamed the call site from `applyCandidateDifficultyHealth()` to
`applyBedrockDifficultyHealth()`, but the private method declaration kept the old name.

No Minecraft/Forge behavior issue was involved.

## Repair

Rename the private method declaration to `applyBedrockDifficultyHealth()`.
No behavior or constant changes are included in the repair.

## Verification

Pending dedicated Forge build + GameTest on the exact repaired generation.

## Lesson

When a behavior label moves from "candidate" to an accepted runtime contract, perform symbol renames atomically. CI correctly caught a documentation/implementation naming drift before runtime acceptance.

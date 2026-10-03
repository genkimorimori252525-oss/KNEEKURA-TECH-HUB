# Bedrock Wither — Failure / Repair Records

Use the Hub's Minecraft Failure/Repair History semantics for product incidents with `origin=OWN_DEVELOPMENT`.

A record should preserve:
- symptom;
- trigger/environment;
- root cause basis (DIRECT_OBSERVATION / AUTHOR_CLAIM / INFERENCE / UNKNOWN);
- affected symbols;
- before/after revision;
- actual repair;
- reproduction and verification evidence;
- regression scope;
- reusable lesson;
- unresolved alternatives.

Do not create fake "success" cases before an incident exists.

## Current cases

| ID | State | Subject |
|---|---|---|
| [BWR-0001](BWR-0001-wildcard-optional-compile.md) | VERIFIED_FIXED | Java wildcard `Optional` compile boundary |
| [BWR-0002](BWR-0002-json-only-skull-impact.md) | REPAIR_IN_PROGRESS | JSON-only inference incorrectly removed skull impact damage |
| [BWR-0003](BWR-0003-difficulty-helper-rename.md) | VERIFIED_FIXED | difficulty-health helper rename compile drift |
| [BWR-0004](BWR-0004-spawn-state-zero-frame.md) | REPAIR_IN_PROGRESS | zero/uninitialized spawningFrames skipped spawn sequence |
| [BWR-0005](BWR-0005-java-skull-impact-damage.md) | REPAIR_IN_PROGRESS | Java WitherSkull superclass gave wrong Bedrock difficulty damage |
| [BWR-0006](BWR-0006-volley-gametest-ai-interference.md) | REPAIR_IN_PROGRESS | controller GameTest mixed ambient AI / shared batch interference |
| [BWR-0007](BWR-0007-health-bucket-test-difficulty-assumption.md) | REPAIR_IN_PROGRESS | health-bucket fixture assumed Hard-scale absolute HP |
| [BWR-0008](BWR-0008-living-reload-death-latch.md) | VERIFIED_FIXED (local GameTest) | healthy reload incorrectly finalized future death |
| [BWR-0009](BWR-0009-spawn-visual-sync.md) | VERIFIED_FIXED (local GameTest) | renderer-facing spawn timer was not synchronized |
| [BWR-0010](BWR-0010-cancelled-death-revival.md) | VERIFIED_FIXED (local GameTest) | canceled Forge death corrupted revived combat state |

States are updated only after retained build/GameTest evidence exists. A compile success does not close a gameplay case; a gameplay pass does not imply direct Bedrock parity.

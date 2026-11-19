# BWR-0008 — living reload incorrectly finalized future death

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (bounded local Forge GameTest contract)

## Symptom and trigger

A healthy Wither saved and reloaded entered semantic death after a lethal hit but could not begin or complete its custom death countdown.

Baseline: `c1221d3c6cb46ee719923d9f99abd8739ddb802d`. Tests ran in an isolated cloud Linux Forge 47.2.0 / Minecraft 1.20.1 / Java 17 GameTest server. No user desktop or home CI was used.

## Root cause

Basis: DIRECT_OBSERVATION + source inspection + independent review.

DeathController.restore interpreted zero death ticks in a living save as finalized=true. Both begin() and tickServer() then returned immediately. An inactive sequence was confused with executed terminal removal.

## Repair and exact source

Reset the per-lifetime finalized latch on restore while retaining the saved countdown and visual values. Actual terminal removal still owns setting finalized=true.

Locally verified source commit: `b7fd04b037a4b3eed2450c51fe55c9e3ddfdfcca`. File-level SHA-256 identities are in [the compact receipt](../../evidence/gametest-2026-10-03.json); these bind the tested code independently of later documentation/publication commits.

## RED → GREEN

- Tests: `livingReloadCanFinishDeathSequence; activeDeathReloadPreservesRemainingTicks`
- Before the production change: 21 required tests ran, 19 passed, and only the two new bug-reproduction cases failed with their intended assertions. The mid-death save/load regression already passed and protects preserved progress.
- After the change: `gradle build runGameTestServer` exited 0 and reported **21/21 required tests passed**.
- Independent review found no blocking issue. Entity-data tests use the actual non-default/dirty snapshot and assignValues boundary, with a server-backed replica; they do not launch a real client.

No health, attack, spawn-duration, death-duration, explosion or other Bedrock gameplay constant changed. These tests do not establish direct Bedrock/Tank parity or exact final explosion-count idempotency. Raw logs/worlds/assets are excluded from Git.

## Lesson

No active death sequence is not proof that terminal death side effects have already executed. Persistence must preserve the ability to enter a future lifecycle, not only resume an active one.

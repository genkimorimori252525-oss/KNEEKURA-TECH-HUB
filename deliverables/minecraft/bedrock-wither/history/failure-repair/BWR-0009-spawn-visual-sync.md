# BWR-0009 — spawn skin timer remained client-local

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (bounded local Forge GameTest contract)

## Symptom and trigger

The renderer-facing spawn timer stayed at the constructor value in an entity-data replica instead of following the server countdown.

Baseline: `c1221d3c6cb46ee719923d9f99abd8739ddb802d`. Tests ran in an isolated cloud Linux Forge 47.2.0 / Minecraft 1.20.1 / Java 17 GameTest server. No user desktop or home CI was used.

## Root cause

Basis: DIRECT_OBSERVATION + source inspection + independent review.

SpawnController changed only runtimeState.spawningFrames. The renderer getter read that ordinary local field; SynchedEntityData carried no spawn countdown.

## Repair and exact source

Add a synchronized spawn timer with the same 220 default on server and replica, route all four controller writes through one setter, and have the visual getter read synchronized data. Default 220 makes completed zero part of an initial non-default snapshot, covering late tracking.

Locally verified source commit: `b7fd04b037a4b3eed2450c51fe55c9e3ddfdfcca`. File-level SHA-256 identities are in [the compact receipt](../../evidence/gametest-2026-10-03.json); these bind the tested code independently of later documentation/publication commits.

## RED → GREEN

- Tests: `spawnVisualTicksFollowEntityDataSnapshots`
- Before the production change: 21 required tests ran, 19 passed, and only the two new bug-reproduction cases failed with their intended assertions. The mid-death save/load regression already passed and protects preserved progress.
- After the change: `gradle build runGameTestServer` exited 0 and reported **21/21 required tests passed**.
- Independent review found no blocking issue. Entity-data tests use the actual non-default/dirty snapshot and assignValues boundary, with a server-backed replica; they do not launch a real client.

No health, attack, spawn-duration, death-duration, explosion or other Bedrock gameplay constant changed. These tests do not establish direct Bedrock/Tank parity or exact final explosion-count idempotency. Raw logs/worlds/assets are excluded from Git.

## Lesson

A server-correct timer does not establish client-correct visuals. Test normal entity-data updates, initial non-default snapshots, late tracking and NBT restoration across the same boundary the client consumes.

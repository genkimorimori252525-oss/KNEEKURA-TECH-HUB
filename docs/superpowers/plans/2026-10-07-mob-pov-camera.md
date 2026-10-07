# Mob POV Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in live mob viewing, explicit one-image retrieval and reliable return without continuous recording.

**Architecture:** Existing sealed owner transport authorizes a dedicated client camera session. Pure lifecycle/command validation surrounds Forge rendering and the existing image writer; one camera claim serializes cardinal and POV.

**Tech Stack:** Java17/Forge1.20.1, Node native test runner, Python pytest; no added dependency.

**Spec:** `docs/superpowers/specs/2026-10-07-mob-pov-camera-design.md`.

## Global Constraints

- `mob-eye-live-v1`: fov30..100, viewport64..2048, captures0..16; cardinal unchanged.
- At most32 sequential immutable camera operations/run; duration1..120000ms capped by lease; one requested PNG<=4MiB.
- No constant frame storage/buffer, server tick hold, mob AI/transform writes, new dependencies or original-world changes.
- Existing owned identity, request/source/material/world binding, finite lease and durable evidence remain required.
- Execute inline now per user instruction; local branch only, unrelated changes preserved.

## Review Focus

- External camera/screen/world replacement must not restore stale objects or overwrite another operation.
- Expiry during queued client work or image delivery must not reactivate a closed session.
- Duplicate/out-of-order command files and simultaneous cardinal capture must not repeat or overlap effects.
- Mob death/unload/type/UUID/dimension mismatch must terminate viewing without target mutation.
- View-only must create zero frame artifacts; asynchronous server samples must not claim same-tick alignment.

### Task 1: Feedback audit and source/design

**Files:** `docs/AI-FEEDBACK.md`, `docs/PROJECT-GUIDE.md`, this plan/spec.
**Interfaces:** produces approved rig/budget/lifecycle invariants for Task2; retains original AF IDs/history.
- [x] Read AF0001..0011, current TANK_CORE/cardinal/owner source; baseline44 Node checks PASS.
- [ ] Append audit and approval history; distinguish fixture sizing, player acquisition, camera visualization and source availability.
- [ ] Save design/plan and isolated source base; commit docs explicitly.

### Task 2: Camera work unit

**Files:** Python `minecraft/experiment_contract.py`; LAB `evidence/visual-request-contract.mjs`; `bridge/owner-prelaunch.mjs`, `owner-control-cli.mjs`, new `bridge/mob-pov.mjs`; Forge `KneekuraDebugMobPovSession/Commands/Camera/Owner`, `KneekuraDebugCameraOwnership`, existing `OwnerInputs/Connection`, `CardinalCapture`, evidence writer routing; relevant Python/Node/Java tests.
**Interfaces:** `publishMobPovCommand({runDir,envelopeHash,commandIndex,operation,subjectUuid?,durationMs?})` publishes inert intent; Java command parser validates exact input and actual Arena state; client attach/snapshot/return futures yield finite completion metadata.
- [ ] Write failing rig/permission/transport tests and pure Java lifecycle tests. Run and retain RED for missing capability.
- [ ] Implement strict validator parity, safe transport, client camera claim/lifecycle and actual owner/snapshot budget binding.
- [ ] Exercise view-only zero-write, stale ownership/world/subject, expiry, duplicate/order, snapshot delivery/conflict cases. Run grouped GREEN with related existing suites.
- [ ] Compile actual Forge code once after the coherent unit. Preserve diagnostics, fix actual failures and commit.

### Task 3: Native verification and handoff

**Files:** LAB mob POV usage/verification docs and finite native tooling where needed; shared guide/feedback; this ledger.
**Interfaces:** consumes Task2 CLI/runtime and exact built source; produces reproducible retained pilot evidence and scoped results.
- [ ] Launch one bounded fresh private TANK_CORE copy with source-bound debug build; exercise attach/snapshot/return and zero default capture; inspect raw frame, native ticks and restore/cleanup/original hashes.
- [ ] Run relevant full configured suites once, recording environmental skips/failures separately.
- [ ] Obtain one fresh whole-branch review per executing-plans; fix material findings with regressions.
- [ ] Record exact source/artifacts/limits and update guide/feedback. Keep NaturalGhast unchanged in this task.

## Ledger

2026-10-07: initial plan. User approved intent and directed audit then immediate implementation. Native inline execution preserves that instruction over repeated skill handoff prompts.
Pre-flight: Task1 spec invariants match Task2 validators and Task3 acceptance; snapshot mode does not reuse cardinal4 receipts; no shared-name conflict identified.
Rulings: see spec; append new decisions and verification outcomes here.

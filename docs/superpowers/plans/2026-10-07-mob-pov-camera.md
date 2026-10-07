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
- [x] Append audit and approval history; distinguish fixture sizing, player acquisition, camera visualization and source availability.
- [x] Save design/plan and isolated source base; commit docs explicitly.

### Task 2: Camera work unit

**Files:** Python `minecraft/experiment_contract.py`; LAB `evidence/visual-request-contract.mjs`; `bridge/owner-prelaunch.mjs`, `owner-control-cli.mjs`, new `bridge/mob-pov.mjs`; Forge `KneekuraDebugMobPovSession/Commands/Camera/Owner`, `KneekuraDebugCameraOwnership`, existing `OwnerInputs/Connection`, `CardinalCapture`, evidence writer routing; relevant Python/Node/Java tests.
**Interfaces:** `publishMobPovCommand({runDir,envelopeHash,commandIndex,operation,subjectUuid?,durationMs?})` publishes inert intent; Java command parser validates exact input and actual Arena state; client attach/snapshot/return futures yield finite completion metadata.
- [x] Write failing rig/permission/transport tests and pure Java lifecycle tests. Run and retain RED for missing capability.
- [x] Implement strict validator parity, safe transport, client camera claim/lifecycle and actual owner/snapshot budget binding.
- [x] Exercise view-only zero-write, stale ownership/world/subject, expiry, duplicate/order, snapshot delivery/conflict cases. Run grouped GREEN with related existing suites.
- [x] Compile actual Forge code after the coherent unit and material review fixes. Preserve diagnostics, fix actual failures and commit.

### Task 3: Native verification and handoff

**Files:** LAB mob POV usage/verification docs and finite native tooling where needed; shared guide/feedback; this ledger.
**Interfaces:** consumes Task2 CLI/runtime and exact built source; produces reproducible retained pilot evidence and scoped results.
- [x] Launch bounded fresh private TANK_CORE copies with source-bound debug builds; exercise attach/snapshot/return and zero default capture; inspect raw frame, native ticks and restore/cleanup/original hashes. Preserve failed trials; final sealed audit establishes the scoped facts below.
- [x] Run relevant full configured suites once, recording environmental skips/failures separately.
- [x] Obtain one fresh whole-branch review per executing-plans; fix material findings with regressions.
- [x] Record exact source/artifacts/limits and update guide/feedback. Keep NaturalGhast unchanged in this task.

## Ledger

2026-10-07: initial plan. User approved intent and directed audit then immediate implementation. Native inline execution preserves that instruction over repeated skill handoff prompts.
Pre-flight: Task1 spec invariants match Task2 validators and Task3 acceptance; snapshot mode does not reuse cardinal4 receipts; no shared-name conflict identified.
Rulings: see spec; append new decisions and verification outcomes here.

2026-10-07 completion evidence: local implementation86555f8, native correctionsb71f2f7/a271bd9/b7ab776/546ebfe. Related Node99/99; Python97 contracts +147control PASS/3 Windows symlink deselected; Java18+8 and genuine-Gson Node/Java ordinary/Tank/mob fixtures; actual Forge47.2 compile PASS. Broad Node515 =511 PASS/3 FAIL/1 SKIP, Windows symlink/inherited-pipe limitations; portable JVM runner blocked at earlier symlink fixture. No security guard relaxed.

One fresh whole-branch review: Critical0/Important2/Minor1. Fixed both Important findings with regressions: raw-frame overlay suppression; late canonical PNG retrieval/sealing while retaining UNKNOWN. Deferred numeric validatedAtNanos negative/unsafe clock availability issue. Review declined native camera judgment until measured (now scoped sealed audit below); moving/dead/unloaded/external-camera native remains NOT_RUN; existing Windows failures retained; AI perception/NaturalGhast outside scope.

Native frozen-Reimu acceptance, LAB546ebfe / host7f1496: `C:/temp/kneekura-mob-pov-20261007/mob-pov-4k50LD/sealed-audit.json` PASS. Default0PNG, ticks141->161, one640x480/FOV60/47598-byte PNG, explicit/EXPIRED RESTORED, EVIDENCE_COMPLETE/dropped0/original85 unchanged. Full exact hashes and source revisions: AF-0011 and MOB-POV.md. Original pilot FAIL retained: expiry assertion preceded canonical arrival; read-only audit independently checks late sealed evidence. Future corrected waiting sequence not rerun end-to-end. Earlier harness/viewport/clock/cache failures retained, never overwritten. Native camera scope excludes moving/dead/unloaded/external-camera/screen/world cases; static/pure tests do not certify them.

Rulings and costs (including spec/scratch decisions):

- Separate live POV rig from frozen cardinal: correct time contract; cost: future new-artifact/validator maintenance.
- View plus one PNG first, defer clips: explicit retrieval without extra storage/dependencies; cost: later bounded sequence/encoder work.
- Retain local branch without push/merge: requested implementation scope; cost: later integration.
- Continue approved audit-then-implementation without repeated handoff approval: explicit user instruction; cost: design corrections stay on isolated branch.
- Run one fresh source review alongside native acceptance: independent source/evidence work; cost: coverage notes reconciled after native result.
- Use independent immutable sealed audit instead of another launch merely to turn the pilot report green: every stated native fact is present; cost: corrected future waiting sequence lacks end-to-end rerun.
- Preserve task scratch/private failed trials under user's deletion rule: reviewable failure history; cost: retained local disk usage.

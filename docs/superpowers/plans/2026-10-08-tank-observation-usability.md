# Tank observation usability implementation plan

2026-10-08. User authorized independent review, plan amendments and inline implementation. Use `superpowers:executing-plans`; one fresh whole-change review at completion.

**Goal:** Practical finite room discovery and requested cameras for the accepted moving NaturalGhast.

**Architecture:** Separately seal observation scope; reuse private owner transport, canonical evidence and camera ownership. Preserve v1, mutation grants, complete source pins and all failed/unknown history. Node ESM/Python/Java17, Minecraft1.20.1/Forge47.4.10; no dependencies or additional MOD.

**Spec:** [Observation/camera design](../specs/2026-10-08-tank-observation-usability-design.md).

## Constraints and review focus

- Preserve product source182fcb7 and accepted JAR SHA2566c5d2156e9ad83d437d3106721221c13e5221531c1518a069274564364ab3bca. No Ghast movement/AI/balance edits.
- Reuse `codex/mob-pov-camera-20261007`, basefab220d. Original/finalized worlds: raw-hash inputs only; native trials: fresh disposable copies. Existing85-file baseline applies to its fixture only.
- Half-open interior differs from physical shell and action authority. Observation edges1..64, volume≤65536, entities1..64, owner-wide samples1..8, passenger depth≤8, transport≤64KiB (payload reserves4KiB headroom).
- Before/after exact private integrated-server/world/material/request/lease checks; no chunk loading, entity registration/mutation, renewal, implicit images/history, push/merge or configuration replacement.
- Boundary-crossing bodies and negative chunk coordinates; PARTIAL absence semantics; immutable ordered budgets and original-slot reconciliation; external camera ownership and late frames; unchanged normal Player attack/use/input.
- Verify coherent work units together; do not launch or rerun full suites after every small edit.

## Task1: Sealed observation and bounded discovery

Node: new `tank-observation.mjs`, `tank-roster.mjs`; owner preparation/control CLI, evidence lane/finalization. JVM: new `KneekuraDebugTankObservation`, `KneekuraDebugTankRosterOwner`; owner inputs/gate/connection/writer. Python: control/CLI/source closure. Tests alongside existing contracts.

- [x] Failing then passing scope/recipe/permission/linkage, AABB/local xyz, partial limits and immutable slot tests.
- [x] Seal `control/owner-tank-observation.json`; bind hash in owner envelope/snapshot, independently of action bounds. Current native saved recipe supports Overworld only; reject other dimensions consistently.
- [x] Publish finite `tank_roster(sampleIndex)` slots00..07; native read emits `TANK_ROOM_ROSTER`, canonical exact-line hash and durable receipt after gate checks. Inspection never redispatches.
- [x] Add Python/Node routes and exact36-file closure. Grouped source and genuine JVM checks; report Windows symlink privilege limits separately.
- [x] Complete bounded A–D native acceptance and English guide/feedback reconciliation; see acceptance scope below.

## Task2: Retained camera diagnostics and fixed v2

New Node `camera-plan.mjs`, `capture-bundle.mjs`; existing capture adapter/contracts/compiler/packet/geometry; Python rig/control routes; JVM capture request/session/owner/renderer.

- [x] Retained-only plan, no consumed slots; predicted retained AABB/frustum coverage and UNKNOWN occlusion. No fresh native raycast.
- [x] `inspect-capture`/`capture-bundle`: original-slot raw PNG/hash/state/restoration references, fixed ordered views, COMPLETE/PARTIAL/UNKNOWN. Optional new contact-sheet HTML outside retained runs.
- [x] Versioned `tank-cardinal-4-snapshot-v2`: four-image cost, detached calibrated camera, existing barrier; inward1.5-block eye inset/center height; reject small/blocked/unloaded scope without mutation. Preserve v1 formulas.
- [x] Scope hash and separate observation bounds in v2 metadata; actual pose/matrices/state/restoration validation; cross-language contract and genuine Forge compilation.
- [x] Fresh private native roster and four-frame acceptance, final roundtrip checks and review.

## Task3: Safe moving-subject POV and acceptance

Read pinned mapped input/render/pick ordering first. Proposed opt-in `mob-eye-observe-v2` would use a detached render-only eye transform, exact registered living Mob/body-contained observation scope, finite existing camera claim and lease. Restore Player camera and Player-derived `hitResult` before normal dispatch. No Player/Mob transforms, target, AI, game mode or input suppression. Preserve v1 spectator semantics.

- [x] Verify mapped source: render START → gameRenderer.render → render END → window.updateDisplay; tick START → gameRenderer.pick → handleKeybinds. MouseHandler rotates Player; render-time camera-derived hitResult is the concrete risk.
- [ ] Implement/test detached render lifecycle and prove real attack/use/input, moving view and external-camera ownership before exposing v2. **BLOCKED / NOT_RELEASED**: required native input proof is NOT_RUN. Reviewed fallback permits A–D completion while E stays blocked. Do not relax v1 or advertise v2 acceptance.
- [x] Add finite A–D native pilot `bridge/native/run-tank-observation.mjs`: exact accepted JAR, fresh saved fixture, original raw audit, two requested room reads and one four-image set; no product build/auxiliary MOD.
- [x] Run bounded A–D native acceptance, preserve failures and actual shutdown/finalization.
- [x] One fresh whole-change review; two Important findings reproduced/fixed, affected checks pass. English guide/AF updated; requested Markdown mirrored after original before-hash verification as final handoff.

## Review rulings

Adopt all seven external amendments: explicit bound semantics; owner-wide budget; PARTIAL missing-not-absent; discovery then explicit subject selection; predicted/native/unknown provenance; detached input-safe presentation; structured/derived/raw-reference artifact roles. Qualifications: owner already rejects request-hash substitution, and MouseHandler turns Player, so neither is claimed as a demonstrated exploit. External reviewer could not access unpushed7006c51; local verification is separate.

E remains blocked because no native Player input/hitResult safety proof exists in this unit. Cost: live eye presentation with a survival combat target is deferred; bounded roster and inward fixed cameras remain available. Future E work must implement and exercise its lifecycle before enabling the mode. Preserve accepted swimming throughout.


## Result

A–D bounded native PASS at source2e7821d; [acceptance and limitations](../reports/2026-10-08-tank-observation-acceptance.md). Two complete roster samples, one complete/restored four-frame set, clean owned exit and full evidence seal. Original85/JAR unchanged. This active Ghast was stationary between samples; moving-POV remains unproved. E stays BLOCKED/not released. Source Node38+compatibility67, Python focused/paired14 and JVM7+6 checks pass; Windows symlink setup limits remain explicit. No push/merge or worktree removal.

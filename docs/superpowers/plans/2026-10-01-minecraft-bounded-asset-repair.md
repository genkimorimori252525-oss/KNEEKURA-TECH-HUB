# Minecraft Bounded Asset Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Source status:** Implemented and focused-tested; independent integration review and actual hosted editor acceptance remain separate pending gates. Legacy records stay unchanged.

**Goal:** Repair one owned Celestial Staff part, UV face, texture rectangle or display component and retain comparable Before/After evidence with independent allowed-delta checks.

**Architecture:** Extend the existing guarded editor session and Store/CAS. An opt-in capture seals generation zero in the still-owned disposable project; four separate operations produce one next generation each. Pure Python validators independently compare complete snapshots and export equivalence; neither capture nor structural validity grants visual or runtime acceptance.

**Tech Stack:** Python 3.11+ standard library, existing Store/CAS, pinned Blockbench 5.2.1/provider JavaScript, pytest and Node test fixtures.

**Spec:** `departments/minecraft/mod-ai/DEFERRED-IMPROVEMENTS-2026-09-30.md`, Candidates 1–3, selected by the user after the original completion gate. This plan defines the newly selected bounded scope; its implementation must not rewrite historical acceptance.

## Global Constraints

- Preserve the existing request hash, project UUID, registry/token authority, provider source pin and Store/CAS.
- Keep default `run_session` behavior and schema-1 captured evidence readable/exportable. Legacy view labels are insufficient to establish comparability.
- Only the same still-owned, unexpired editor project can continue into repair. No historical-session adoption, arbitrary project import, hierarchy, animations, scripts, paths, URLs, brushes, plugins or external publication.
- Initial repair scope is the owned static Java-item Celestial Staff. Retain the existing 1..128 cube, 16..256 texture dimension, 32-color palette, sequence, response and lease bounds; reject rather than silently truncate oversized snapshots.
- Generation zero becomes immutable once sealed. Each confirmed repair advances exactly one generation. Capture/inspection does not advance asset generation.
- Require the exact baseline receipt/snapshot hash, request, project, generation, stable logical target and old value (or old region hash).
- Store creation-time native object identity and UUID bindings. Names initialize immutable logical IDs; later lookups never fall back to a name.
- Independently compare every unrelated native/model field and every out-of-rectangle decoded RGBA pixel. A success response alone is insufficient.
- UNKNOWN poisons the session. No automatic mutation retry, rollback, unseal, adopted replacement object or late-completion success.
- No new database, scheduler, canonical truth plane or permission grant. `blockbench.py` remains the unchanged read-only M1 probe.
- Actual editor and in-game acceptance remain separate from fixtures, export checks and paired-view comparability.

## Review Focus

1. A native cube or texture is replaced by a different object with the same UUID/name: reject before mutation and quarantine drift (Task 2)
2. A provider changes an unrelated nested field or an adjacent pixel while reporting success: quarantine and fail independent Python validation (Tasks 1–3)
3. Snapshot hashing awaits while UI state changes: check complete state again synchronously immediately before invoking a mutator (Task 2)
4. Camera refit, frustum, viewport, render dimensions or generation differ although view labels match: retain evidence but report NON_COMPARABLE (Task 4)
5. An uncertain response arrives late or client evidence storage fails after the editor changed: never replay; retain only confirmed evidence and expose read-only reconciliation (Task 3)

## File Structure

- Create `src/kneekura_tech_hub/minecraft/asset_mutation.py`: strict mutation/snapshot validation, bounded PNG RGBA decoding, exact expected-delta derivation and independent verification
- Create `src/kneekura_tech_hub/minecraft/asset_comparison.py`: pure same-view/same-lineage evidence comparison; no aesthetic score
- Modify `src/kneekura_tech_hub/minecraft/asset_guard.py`: owned native bindings, seal/snapshot and four operations, frozen-camera capture metadata
- Modify `src/kneekura_tech_hub/minecraft/asset_session.py`: optional generation capture, existing transport reuse and one-shot repair orchestration
- Modify `src/kneekura_tech_hub/minecraft/asset_export.py`: schema-2 lineage/effective-state validation while retaining schema-1 rules and no-overwrite output
- Create `tests/test_minecraft_asset_mutation.py`, `tests/test_minecraft_asset_comparison.py` and a focused Node repair fixture
- Extend existing asset session/export/guard tests as needed without weakening legacy assertions
- CLI/task facade changes and actual-editor dispatch belong to the integration owner, not this work unit

## Contract Decisions

`run_session(store, registry, private_config, plan, *, retain_generation=False) -> dict` preserves the default. When true, it obtains a sealed snapshot before capturing and writes a schema-2 `asset_session_capture` receipt with `generation`, `snapshot_hash`, `parent_receipt_hash` and `mutation_hash` (the latter two are null at generation zero).

`run_mutation(store, registry, private_config, base_receipt_hash, mutation) -> dict` validates all local inputs before network use, verifies the live snapshot against the sealed baseline, sends exactly one mutation and captures the resulting generation. It accepts no retry policy.

`validate_mutation(store, base_receipt_hash, value) -> dict` accepts exactly schema version, request hash, project UUID, expected generation, expected snapshot hash, operation, target, expected and value. It derives the allowed delta; callers cannot supply an expanded allowlist.

Four operation/target forms:

- `part_edit`: `{part_id, property: from|to, axis: 0|1|2}`; expected/value are one finite coordinate in −16..32; resulting bounds remain nondegenerate
- `uv_edit`: `{part_id, face: north|south|east|west|up|down, texture_id: atlas}`; expected/value are one bounded nondegenerate UV rectangle
- `texture_edit`: `{texture_id: atlas, rect: [x0,y0,x1,y1]}`; expected is the SHA-256 of the exact old rectangle's row-major RGBA bytes; value is one existing palette color; integer rectangle and opaque fill only
- `display_edit`: `{slot, property: rotation|translation|scale, axis: 0|1|2}`; existing slots only, one finite component; rotation ±180, translation ±80, scale >0..4

A full snapshot includes request/project/generation, immutable logical/native bindings, complete native and model JSON plus actual decoded RGBA texture bytes. Hash the exact canonical JSON text emitted by the guard and store those bytes unchanged; do not assume Python and JavaScript format every finite number identically. Before/After artifact hashes refer to exact retained captures. The independent verifier compares the complete expected snapshot, including fields outside the allowlist, and checks snapshot/native/model/PNG correspondence.

The guard internally calls only reviewed `edit_element`, `set_cube_uv` or fixed rectangle `paint_texture` arguments. Display edits use the pinned existing `DisplaySlot.extend` API with `Undo.initEdit({display_slots:[slot]})`. Provider UUID-or-name fallback must be defeated by exact owned identity validation before dispatch.

## Task 1: Pure snapshot, mutation and pixel-delta contracts

**Files:** `asset_mutation.py`, `tests/test_minecraft_asset_mutation.py`

**Interfaces:** Produce `validate_snapshot(value: dict) -> dict`, `validate_mutation(store, base_receipt_hash: str, value: dict) -> dict`, `expected_snapshot(before: dict, mutation: dict) -> dict`, `verify_delta(before: dict, after: dict, mutation: dict) -> dict`, and `decode_png_rgba(raw: bytes, dimensions: list[int]) -> bytes`.

- [x] Write failing tests for the four exact operation forms, stale identities/hashes/values, unknown fields, bad numbers, degenerate bounds/UVs, unknown face/slot/texture and non-palette colors
- [x] Write failing full-snapshot tests: one intended change passes; any unrelated geometry, native flag, UV face, texture pixel, display slot, native ID, outliner or root-field change fails
- [x] Write bounded PNG tests for RGB/RGBA and scanline filters 0..4, CRC/size/trailing-data/decompression failures, plus one adjacent-pixel tamper
- [x] Run `PYTHONPATH=src pytest -q tests/test_minecraft_asset_mutation.py` and retain the initial failure
- [x] Implement only the strict contracts, exact operation-specific expected deltas, and standard-library PNG reconstruction
- [x] Re-run the focused suite and retain its result

## Task 2: Owned guard generation and exact one-operation edits

**Files:** `asset_guard.py`, focused Node repair fixture, `tests/test_minecraft_asset_guard.py`

**Interfaces:** Extend the existing `kneekura_asset` operation allowlist with `snapshot`, `part_edit`, `uv_edit`, `texture_edit`, `display_edit`. Preserve outer authentication/sequence/project envelopes and default legacy status shape.

- [x] Write failing Node tests for creation-time object/UUID bindings, seal generation zero, one-step generation advance and exact generated provider parameters
- [x] Write failing missing/duplicate/recreated-target, wrong request/project/generation/hash/value, unrelated-drift, UI-change-during-hash, concurrent-call and late-timeout tests
- [x] Run the existing guard test driver and observe the new failures
- [x] Implement complete snapshot/seal checks and the four narrow operations. Use existing deadline/quarantine behavior; immediately revalidate after any awaited hash and before calling the provider
- [x] Verify only the selected scalar/face/rectangle/slot component changed before committing the next generation; persist immutable bindings and reject post-seal construction operations
- [x] Run legacy and new Node/pytest guard tests; preserve raw-route denial coverage

## Task 3: One-shot session continuation and immutable receipts

**Files:** `asset_session.py`, `tests/test_minecraft_asset_session.py`, mutation tests

**Interfaces:** Produce the two session signatures above; reuse `_registry`, `_command`, `_receipt`, existing config and Store pins. Schema-2 receipts retain the original request/plan/provider fields and add the lineage fields listed above.

- [x] Write failing tests for an opt-in sealed baseline followed by each confirmed mutation, with identical project/native IDs and exactly the next generation
- [x] Write failing transport-loss/UNKNOWN/stale-baseline/changed-project/partial-capture tests; assert no automatic second write and no false finalized receipt
- [x] Run focused session/mutation tests and observe failure
- [x] Implement optional baseline sealing and continuation over the current OPEN status/next sequence only. Compare live full snapshot to the retained baseline before dispatch
- [x] Capture after the one confirmed edit, independently verify all bytes/fields, then store complete receipt closure and pins. Preserve `NOT_RUN` visual/runtime verdicts
- [x] Run old session tests unchanged where possible and the new one-shot failure matrix

## Task 4: Frozen camera metadata and honest comparability

**Files:** `asset_guard.py`, `asset_session.py`, `asset_comparison.py`, comparison/guard tests

**Interfaces:** Produce `compare_captures(store, before_receipt_hash: str, after_receipt_hash: str) -> dict`. Its result has bounded reasons, exact receipt/artifact hashes, generations and per-view `COMPARABLE`/`NON_COMPARABLE`, without quality verdicts.

- [x] Write failing tests for same camera/projection/frustum/viewport/render dimensions and changed silhouette, plus one-at-a-time mismatch/missing-metadata/missing-view/stale-generation cases
- [x] Write a legacy schema-1 test requiring `NON_COMPARABLE` even when view names and PNG dimensions happen to match
- [x] Run focused comparison and host-adapter tests and observe failure
- [x] At the generation-zero baseline, freeze actual camera position/quaternion/up, controls target, perspective/orthographic projection and projection parameters, viewport/canvas dimensions and rendering settings. Capture each subsequent generation using the stored frame without the provider's geometry-dependent `applyAngleName` refit
- [x] Validate the exact supported pinned screenshot path and its cropping behavior; do not assume the requested 320×320 size equals raw viewport size. Include actual output PNG dimensions
- [x] Persist frame metadata and generation with the image. Compare exact metadata and valid lineage; mismatches stay inspectable but non-comparable
- [x] Run the focused suite, including concurrent render metadata drift

## Task 5: Independent export equivalence and backward compatibility

**Files:** `asset_export.py`, export/mutation tests

**Interfaces:** Existing `materialize_asset(store, receipt_hash, *, parent)` accepts both schema versions. V2 checks the sealed initial plan and bounded parent/mutation chain before validating the resulting native/model/PNG state.

- [x] Write failing tests exporting each valid repaired generation and rejecting changed unrelated data, forged parent/target/generation/hash, native/model UV scale mismatch and native/PNG mismatch
- [x] Keep legacy export and no-overwrite tests, including a legacy capture without camera metadata
- [x] Run focused export tests and observe failure
- [x] Implement v2 effective-state validation through a bounded chain, preserving all existing static-item/version/resource/PNG/native constraints and fixed initial display policy
- [x] Re-run all asset tests plus the relevant task facade tests to detect receipt compatibility regressions

## Task 6: Review and actual-editor acceptance preparation

**Files:** This plan; integration owner controls harness/workflow edits and acceptance records

- [x] Run all focused asset tests with Node available and adjacent task-facade checks; the integration owner runs the repository aggregate after the slice freezes
- [x] Review the exact diff for unrequested routes, broadened permissions, leaked private paths/tokens and weakened legacy checks
- [ ] Commit only this work unit's exact files; return tested commit, test totals, failures/skips and diff for independent review
- [ ] Do not mark actual editor acceptance complete from fixtures. Reuse `tools/ci/mod_ai_blockbench_live.py`, `tools/ci/blockbench_cdp.mjs` and `.github/workflows/mod-ai-blockbench.yml` for a later authorized actual run

### Concrete acceptance sequence

Build the existing 16-part Celestial Staff in a fresh isolated editor, opt in to a sealed generation-zero capture, and retain that canonical initial evidence. For each pair below, introduce one declared bounded fault through the same guarded API, capture Before, repair it through the API, capture After and re-export into a new directory:

1. `star_up.to[1]`: 30 → 28.5, restoring the halo air gap
2. `star_core/north` UV: `[0,0,4,4]` → `[24,24,28,28]`, restoring the purple face
3. `atlas` rectangle `[24,24,32,32]`: gold `#d4af37` → accent `#864fc7`
4. `thirdperson_righthand.translation[1]`: 6 → 4, restoring the initial held-item display transform

These are explicitly injected regression faults based on the earlier missing-accent/solid-halo problems, not undiscovered defects in the accepted staff. Each repair must retain native identities, alter only its declared fields/pixels and restore the initial effective state. Include a separate `halo_top.to[1]` 32→31→32 scene-bounds control that proves the camera was not refitted (ten total mutations, under the 32-generation bound). View matching establishes comparison conditions, not visual quality; the display edit proves only structural held-slot/native/export correspondence; normal Blockbench preview does not prove in-game hand appearance.

The supported existing actual-editor route pins Blockbench 5.2.1 (source `e2ede0809ee6bc91f374ac7e00d34cffbdf86a14`) and provider `028cdd76589de2e2cea51bfd79495b50a3c7d1d2`, verifies the official package hash, uses an isolated profile and software WebGL, and retains read-only failure diagnostics without replay. Use the authorized cloud environment only. Missing editor/display prerequisites are a blocker to live acceptance, not permission to substitute the user's computer or label fixtures as live evidence.

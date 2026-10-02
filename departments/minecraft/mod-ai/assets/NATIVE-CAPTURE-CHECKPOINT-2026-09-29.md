# M2 native capture checkpoint — 2026-09-29

Status: **IMPLEMENTED, AWAITING FRESH FULL-REPOSITORY VERIFICATION.**

This checkpoint continues the deliberate RED recorded in
`LOCAL-AI-HANDOFF-2026-09-28.md`.

## Change

The guarded Blockbench pathless capture contract now distinguishes:

- exported Java item model JSON (`model`);
- editable native Blockbench project JSON (`native`);
- PNG texture bytes (`texture`);
- bounded required-view PNG evidence (`view`).

Native capture does not accept a caller filesystem path. The guarded host uses
Blockbench's project codec in memory and returns bounded UTF-8 JSON through the
same authenticated/request-bound operation. Raw `save_project`, `export_project`,
`export_model`, `load_project`, arbitrary script and plugin-install routes remain
closed.

The session layer validates native JSON independently and retains it in the existing
CAS only after the expected guarded session completes. Structural, visual and runtime
verdicts remain `NOT_RUN`.

## TDD history

The prior hosted RED at executable head
`824a2365a0ac945620f26a15339b352ac0de35f6` was:

- 787 passed;
- 2 failed;
- both failures represented the missing `native` capture interface.

The implementation and the corrected native-content assertion are now on PR #74.
This document intentionally does **not** claim GREEN. Its commit exists to request a
fresh standard hosted regression run against the current branch bytes.

## Remaining M2 acceptance

Even a green hosted suite will still be fixture/protocol evidence, not live Blockbench.
The following remain required before M2 can be called complete:

1. guarded derivative prepared from the exact pinned upstream source;
2. disposable desktop Blockbench load;
3. one Celestial Staff geometry/texture session;
4. required-view capture and host-AI visual review;
5. native/model/texture byte capture checked against the live project;
6. final narrow materialization/export boundary with no-overwrite/path-scope controls.

Do not infer Minecraft, Windows-input, network or performance acceptance from this slice.

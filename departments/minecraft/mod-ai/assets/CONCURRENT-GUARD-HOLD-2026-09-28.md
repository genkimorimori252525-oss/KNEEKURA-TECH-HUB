# Concurrent M2 change detected — integration hold

Status: **REVIEW-ONLY CANDIDATE; NOT INTEGRATED INTO PR #74**.
This notice supersedes any implication that this branch's writer is the active
M2 implementation. Do not load its generated plugin or merge this branch as-is.

## Observed refs

- Starting PR #74 head: `a4b195a0466ec59fb7e57a4eae1fff45e9f9603f`.
- This session's independently tested writer commit:
  `796f738a3f77be25404c77fd147ce85131bd78db`.
- During publication preflight, #74 had advanced eight commits to
  `29f4b925abc16a3f2bb6bd185640eef8f0e56d04`.
- The concurrent diff adds `asset_guard.py`, its Python/Node tests and three
  guard implementation/verification records. It touches a materially overlapping
  provider-side dispatch and local preparation boundary.
- The last observed commit is titled `Extend RED coverage to pathless Blockbench
  capture adapter`. Its name alone is not evidence that the current suite passes
  or fails, but it is not a completed integration handoff either.

The expected head check caught this before any update to PR #74. No force push,
parent-branch change, main merge or replacement of the concurrent work occurred.
This candidate is preserved on `jolly/minecraft-mod-ai-sealed-writer-2026-09-28`.

## Reconciliation, not a second production guard

The current #74 `asset_guard.py` must be read at its latest complete revision
before continuing. It already provides request-bound provider dispatch, bounded
geometry creation, project inventory checks, safe package placement and explicit
removal of upstream autostart. Its `kneekura_asset` operation/sequence protocol
is different from this candidate's sealed `kneekura_asset_build` protocol.
Do not run both, add both as active backends, or mistake protocol similarity for
interoperability.

Preserve the existing guard's strengths. In particular, this candidate's source
composer has NOT yet removed the source autostart block, and its POSIX file
checks are less comprehensive than the concurrent directory-descriptor guards.
Consequently this branch is not an alternate approved live-installation path.

The independently useful work to port is the strict export-byte consistency
boundary in `asset_artifacts.py`, the explicit pixel-grid/staff blueprint, and
regressions for native/Java/texture/view mismatches. Consolidate the source/session
preparation and request rehydration rather than keeping parallel implementations.
Then extend the existing guard with bounded texture/display/render/compile-bytes
operations and an explicit client whose uncertainty marker survives a lost reply.
Use the candidate as reviewed source/test material, not as an automatic replacement.

## Evidence and next action

The candidate's selected-file suite passed 88 pytest cases; one case runs 27
Node guard tests against host doubles. Re-run before porting. Exact candidate
bytes and local evidence are in `m2-verification.json`. Those results do not
verify the concurrent #74 implementation or a combined tree. No new full-repository
CI result, full upstream composition or live Blockbench result is claimed here.

Next: identify the authoritative completed #74 head, compare its pathless-capture
work against the candidate, transplant only missing non-duplicate code/tests,
run the combined full suite, and only then perform the real disposable editor
acceptance. Keep M2 open. Preserve M3-M5, Twilight-first/Connector-next and the
existing server observation stack. Do not restart already verified foundations.

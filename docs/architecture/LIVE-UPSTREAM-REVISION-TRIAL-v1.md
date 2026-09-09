# Live Upstream Revision Trial v1

## Purpose

This acceptance proves that the governed upstream-revision path works with real, commit-pinned OSS history rather than only synthetic fixtures.

The trial uses one stable public Source identity:

```text
src:github:salsa-rs:salsa
```

and one real upstream compatibility change in `salsa-rs/salsa`.

The objective is not to make live GitHub the CI authority. The objective is to observe real upstream state once, freeze the exact commit-pinned bytes and provenance identities, and then prove that the existing Hub path preserves both generations without rewriting history.

## Live upstream observation

Live GitHub inspection on 2026-09-10 identified the Salsa MSRV change introduced by:

```text
child commit
  e2304b4342cb10ed453f0f464bdad83f7d159c56
  "bump MSRV to 1.88 (#1283)"

parent commit
  81496d19d42c9d6f4bab876d1f2ac9941ec8992f
```

The relevant file is `Cargo.toml`.

At the parent revision:

```text
line 149
rust-version = "1.85"

tree
5a45c8c185f728d03fdcaf39b842bf28360c7860

Cargo.toml Git blob
cfbd80759370cfa2a7739f3edcc071aebfb94ca1

size
3763 bytes
```

At the child revision:

```text
line 149
rust-version = "1.88"

tree
4bce6a41e07f4413f859a3ad08f2c3e8485bf028

Cargo.toml Git blob
477682f80c520c588a2bb4cfbba2f3a479c56414

size
3763 bytes
```

The GitHub commit diff reports this exact `Cargo.toml` change:

```text
-rust-version = "1.85"
+rust-version = "1.88"
```

## Frozen capture

The acceptance stores:

```text
tests/fixtures/live-upstream-revision/salsa-msrv/Cargo.before.toml
tests/fixtures/live-upstream-revision/salsa-msrv/capture.json
```

`Cargo.before.toml` is the exact parent-revision file captured from GitHub.

The test computes the Git object identity itself:

```text
SHA1("blob " + byte_length + NUL + file_bytes)
```

and requires it to equal the live-observed parent blob SHA.

The child file is deterministically reconstructed by replacing exactly one occurrence of the captured line:

```text
rust-version = "1.85"
```

with:

```text
rust-version = "1.88"
```

The test then requires:

- the resulting byte count to remain 3763;
- the only changed text line to be line 149;
- the resulting Git blob identity to equal the live-observed child blob SHA `477682f8...`.

Therefore the fixture is not merely a prose transcription of the upstream change. Its bytes reproduce the actual Git object identities observed from the public repository.

## Deterministic CI boundary

CI intentionally does **not** fetch GitHub at test time.

Live network state is mutable and would make acceptance non-reproducible. The separation is:

```text
live inspection
    -> establish exact commit/tree/blob identities
    -> freeze commit-pinned capture

CI
    -> verify frozen bytes reproduce those identities
    -> exercise the Hub against the verified frozen capture
```

The capture is evidence for this acceptance test. It is not a permanent runtime authorization to fetch future Salsa revisions.

Any future upstream refresh still requires the normal fresh human exact-revision Authorization.

## Governed real-OSS path

The PostgreSQL acceptance runs the real capture through the existing production path.

```text
stable Salsa Source
    |
    +-- parent 81496d19...
    |     -> human exact Authorization A1
    |     -> bounded Cargo.toml Execution
    |     -> Git blob verification
    |     -> Verified Acquisition Commit
    |     -> immutable Snapshot S1
    |     -> Evidence at line 149
    |     -> Claim C1: declared Rust version 1.85
    |     -> human SUPPORTED
    |     -> human VALIDATED
    |
    +-- child e2304b43...
          -> fresh human Authorization A2
             explicitly supersedes consumed A1
          -> bounded Cargo.toml Execution
          -> Git blob verification
          -> Verified Acquisition Commit
          -> immutable Snapshot S2
          -> Evidence at line 149
          -> separate Claim C2: declared Rust version 1.88
          -> explicit competition review
          -> human SUPPORTED
          -> human VALIDATED

new real upstream evidence
    -> AI may CHALLENGE C1
    -> human SUPERSEDES C1 by C2
```

## One-shot authority remains intact

Real OSS data does not weaken the acquisition authority model.

A1 authorizes only:

- the exact Salsa Source;
- the exact parent commit;
- `Cargo.toml` only;
- selected-files acquisition only.

After its Verified Acquisition Commit, A1 is consumed.

A2 must be a fresh human decision for the exact child revision and must explicitly supersede A1. A2 is also consumed by its own Verified Acquisition Commit.

The live capture does not create automatic permission for later Salsa commits.

## Real Git provenance invariant

The fetch callback used by the acceptance returns both:

- the frozen file bytes;
- the real GitHub-observed Git blob SHA.

The acquisition implementation independently recomputes the Git blob SHA from the bytes. A transcription error, accidental fixture edit, or mismatched upstream identity therefore fails the execution before the bytes can become a verified Snapshot.

The resulting historical chains remain:

```text
C1
  -> Evidence for line 149 / 1.85
  -> immutable Snapshot at 81496d19...
  -> Salsa Source

C2
  -> Evidence for line 149 / 1.88
  -> immutable Snapshot at e2304b43...
  -> Salsa Source
```

C1 is never rewritten to point at the child commit.

## Claim handling

The upstream change creates a new Claim because the reviewed epistemic payload of C1 is immutable.

While both generations are active, Comparison reports multiple active Claims and differing statements. It does not select a winner and does not treat the newer commit as automatic authority merely because it is newer.

Human Support and Validation of C2 must explicitly acknowledge C1 as an active competing Claim.

After C2 is validated:

- AI may move C1 to `CHALLENGED` as a re-verification warning;
- AI may not make the terminal replacement decision;
- a human may mark C1 `SUPERSEDED` by C2 under the existing Disposition Gate.

Supersession changes current knowledge lifecycle. It does not delete the parent-revision evidence chain.

## Acceptance result

The first PostgreSQL CI run passed without modifying production code:

```text
322 passed
```

The real Salsa data therefore exposed no new integration gap in the existing Freshness / Authorization / Verified Commit / Claim lifecycle design.

## Deliberate non-goals

This trial does not add:

- live network access to CI;
- automatic GitHub polling;
- automatic trust in a commit because it is newer;
- automatic refresh Authorization;
- automatic Claim promotion or supersession;
- automatic semantic interpretation beyond the pinned line evidence;
- a latest-wins rule;
- a mutable Snapshot;
- a mutable reviewed Claim;
- a new conflict or freshness table;
- a schema or migration.

## Governing principle

> Real upstream change is admitted as another immutable observation of the same Source. Its provenance must be verified independently, and any change to accepted knowledge remains a governed human decision.

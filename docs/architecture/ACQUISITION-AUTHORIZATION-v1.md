# Acquisition Authorization v1

## Purpose

KNEEKURA TECH HUB deliberately separates three operations:

1. **Selection** — a Source is worth deeper investigation.
2. **Authorization** — an exact bounded upstream scope may be acquired.
3. **Execution** — material was actually retrieved.

Acquisition Authorization v1 implements only step 2.

```text
GitHub discovery
      ↓
metadata-only Source
      ↓
active human SELECT_FOR_REVIEW
      ↓
license + provenance checks
      ↓
Human Acquisition Authorization
      ↓
exact commit + exact file list
      ↓
(no retrieval; no Source mutation)
```

The central invariant is:

```text
AUTHORIZE ≠ RETRIEVED
```

After authorization, the Source still remains:

```text
source.acquisition.level = metadata-only
```

A cross-layer regression proves that Controlled Discovery still rejects SourceSnapshot creation on an authorized-but-not-executed metadata-only Source.

## v1 scope: selected files only

v1 never authorizes `full-source`.

Every grant is fixed to:

```text
acquisition_level = selected-files
```

with an explicit allowlist of 1–32 repository-relative file paths.

There is no directory wildcard, recursive repository permission, or implicit permission for neighboring files.

## Immutable revision boundary

For GitHub Sources, `revision` must be an exact lowercase 40-hex commit SHA.

Moving or ambiguous references are rejected, including:

- `main`
- `master`
- `latest`
- abbreviated SHAs
- uppercase/non-canonical SHA text

The authorization must identify the same upstream revision years later.

## Path boundary

`allowed_paths` is an exact unique list capped at 32 entries.

v1 rejects:

- absolute paths;
- Windows-style backslash paths;
- drive/URI-like colon paths;
- empty path segments;
- `.` segments;
- `..` traversal segments;
- repository control data such as `.git/...`.

Each path is a specific review target, not a capability to explore arbitrary repository content.

## Human authority

Canonical acquisition authorization is human-only in v1.

The acting identity must exactly equal `created_by`.

AI, crawlers, and tools may discover Sources or prepare suggestions, but they cannot grant canonical acquisition authority.

## AUTHORIZE prerequisites

A new `AUTHORIZE` record requires all gates below at decision time.

### Source depth

The Source must still be `metadata-only`.

### Current selection

The referenced `selection_decision_id` must be the one current active decision for the same Source and must be:

```text
SELECT_FOR_REVIEW
```

A historical selection is insufficient. `DEFER` and `REJECT_FOR_REVIEW` block new authorization.

### Resolved declared license

The Source must have:

```text
license.state = KNOWN
```

plus a non-empty `declared_expression`.

A GitHub Search API license hint is never enough. `UNKNOWN`, `CONFLICT`, `REVIEW_REQUIRED`, or `KNOWN` without an actual declared expression cannot grant deeper acquisition authority.

### Exact bounded scope

The authorization must contain:

- `selected-files` acquisition level;
- one immutable revision;
- 1–32 explicit safe relative paths.

## Historical grant is not permanent authority

An authorization record is immutable historical evidence that authority was validly granted **at that time**. It is not an eternal capability.

Before a future executor can consume an AUTHORIZE record, the Hub re-evaluates whether that grant is still **effective now**.

`authorization_effectiveness` fails closed when any current prerequisite has changed. Current blockers include:

- the record is no longer the active authorization;
- the active decision is not `AUTHORIZE`;
- the Source is no longer metadata-only;
- the Source license is no longer resolved as `KNOWN` with a declared expression;
- the referenced `SELECT_FOR_REVIEW` is no longer the current active selection.

Therefore this sequence is safe:

```text
AUTHORIZE valid at T1
      ↓
selection changes to DEFER at T2
      ↓
historical AUTHORIZE remains auditable
      ↓
effective authority becomes false immediately
```

The same applies if licensing becomes unresolved.

This distinction prevents knowledge/governance laundering from the statement:

> "This was once authorized"

into the stronger and potentially false statement:

> "This is authorized now."

`authorized_acquisition_requests` exposes only currently effective AUTHORIZE records. It remains read-only and performs no retrieval.

## Append-only authorization history

`source_acquisition_authorization` records use `aa:` IDs and are append-only.

A Source may have only one active authorization decision in the append-only chain.

Changing scope requires a new `AUTHORIZE` that explicitly supersedes the current active record. The previous record remains in history.

This avoids mutable permission objects whose historical meaning cannot be reconstructed.

## Revocation

Revocation is another append-only record:

```text
REVOKE
```

A REVOKE must supersede the current active AUTHORIZE and repeat its exact scope:

- Source;
- selection decision reference;
- acquisition level;
- revision;
- allowed paths.

Repeating the scope makes the cancelled authority explicit.

### Fail-safe asymmetry

REVOKE does **not** require the old selection to remain active and does **not** require current license metadata to remain favorable.

If selection changes to `DEFER` or licensing becomes questionable, the effective grant is already fail-closed, but an operator can still append an explicit REVOKE for durable audit history.

The rule is intentionally asymmetric:

```text
Granting authority requires all gates.
Invalidating/removing authority must remain easy.
```

## No execution side effects

Creating AUTHORIZE or REVOKE does not:

- mutate Source acquisition level;
- create a SourceSnapshot;
- create Evidence;
- fetch README;
- fetch source files;
- clone a repository;
- execute repository code;
- install dependencies;
- create Claims or Knowledge Entities.

Authorization and execution remain separate systems.

## Persistence

Migration `0006_source_acquisition_authorization.sql` adds append-only PostgreSQL persistence with:

- Source foreign key;
- Source selection decision foreign key;
- `AUTHORIZE` / `REVOKE` decision constraint;
- fixed `selected-files` acquisition level;
- explicit revision;
- JSON allowlist constrained to 1–32 paths;
- rationale;
- human actor provenance;
- one direct successor per old authorization.

`AuthorizationPostgresRepository` extends `SelectionPostgresRepository` only for the `aa:` record family. Existing core record persistence is not rewritten.

## CLI

Authorize exact files without retrieving them:

```bash
kneekura-acquisition-auth authorize \
  src:github:owner:repo \
  --selection-id sd:selection \
  --revision 0123456789abcdef0123456789abcdef01234567 \
  --path README.md \
  --path src/lib.rs \
  --rationale 'Only these two files are needed for architecture review.' \
  --actor-id reviewer
```

Revoke an active authorization:

```bash
kneekura-acquisition-auth revoke aa:authorization \
  --rationale 'Cancel before retrieval.' \
  --actor-id reviewer
```

Read state:

```bash
kneekura-acquisition-auth history --source-id src:github:owner:repo
kneekura-acquisition-auth active --source-id src:github:owner:repo
kneekura-acquisition-auth authorized
```

`active` means active in the append-only authorization chain. `authorized` is stricter: it exposes only active AUTHORIZE records whose current selection/license/Source prerequisites are still effective.

## Security posture

Acquisition Authorization v1 is deliberately conservative:

- human-only;
- selected-files only;
- immutable GitHub commit SHA;
- maximum 32 exact paths;
- path traversal/control-data rejection;
- current human selection required;
- resolved declared license required;
- stale prerequisites invalidate effective authority;
- append-only changes;
- explicit revocation;
- one active authorization chain per Source;
- no acquisition execution.

## Non-goals

v1 does not:

- fetch a file;
- update `Source.acquisition.level`;
- create a SourceSnapshot;
- authorize full-source cloning;
- infer a license from GitHub hints;
- let popularity authorize access;
- let repeated discovery authorize access;
- let AI grant canonical authority;
- automatically select useful files;
- execute repository code.

## Next pressure

The next safe slice is **Authorized Acquisition Execution v1**.

That layer should consume exactly one currently effective AUTHORIZE record, retrieve only its pinned revision and allowlisted paths, verify returned content against the requested revision/path, and record what actually happened separately from the authorization.

A safe execution record should independently answer:

```text
Who selected this Source?
Who authorized acquisition?
What exact immutable scope was authorized?
Which files were actually retrieved?
What hashes did they have?
Did execution fully match authorization?
```

Execution must never silently broaden an authorization when a file is missing, a revision cannot be proven, or repository layout differs from expectation.

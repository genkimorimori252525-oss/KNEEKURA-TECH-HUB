# Acquisition Authorization v1

## Purpose

KNEEKURA TECH HUB now has two deliberately separate upstream gates:

```text
GitHub discovery
      ↓
metadata-only Source
      ↓
Human Source Selection
```

Selection answers:

> Is this Source worth deeper manual investigation?

It must not answer:

> What exact upstream material may the system retrieve?

Acquisition Authorization v1 adds that second governance decision without performing retrieval.

```text
metadata-only Source
      ↓
active human SELECT_FOR_REVIEW
      ↓
license/provenance checks
      ↓
Human Acquisition Authorization
      ↓
exact revision + exact file list
      ↓
(no retrieval; no Source mutation)
```

## Core separation

The Hub treats these as three different operations:

1. **Selection** — worth investigating.
2. **Authorization** — exact bounded material may be acquired.
3. **Execution** — material was actually retrieved.

v1 implements only step 2.

Therefore:

```text
AUTHORIZE
   ≠
retrieved
```

and after authorization:

```text
source.acquisition.level == metadata-only
```

still holds.

A cross-layer regression test proves that Controlled Discovery continues to reject SourceSnapshot creation on the authorized-but-still-metadata-only Source.

## v1 scope: selected files only

Authorization v1 does not support `full-source`.

Every authorization is fixed to:

```text
acquisition_level = selected-files
```

and contains an explicit allowlist of 1–32 repository-relative paths.

This makes authorization bounded and reviewable rather than a general permission to explore a repository.

## Immutable revision requirement

For GitHub Sources, `revision` must be an exact lowercase 40-hex commit SHA.

Rejected examples include:

- `main`
- `master`
- `latest`
- tags used as moving aliases
- abbreviated SHAs
- uppercase/non-canonical SHA text

An authorization should continue to identify the same upstream content years later.

## Path boundary

`allowed_paths` is an exact unique list, capped at 32 entries.

v1 rejects:

- absolute paths;
- Windows-style backslash paths;
- drive/URI-like colon paths;
- empty segments;
- `.` segments;
- `..` traversal segments.

Authorization does not mean "anything reachable from this directory". Each path is one explicitly reviewed repository-relative target.

## Human authority

Canonical acquisition authorization is human-only in v1.

The acting identity must exactly match `created_by`.

AI, crawler, and tool actors may discover metadata and later help prepare suggestions, but they cannot grant canonical acquisition authority.

## AUTHORIZE prerequisites

An `AUTHORIZE` record requires all of the following at decision time.

### 1. Source still metadata-only

The Source must not already be at a deeper acquisition level.

### 2. Current selection

The referenced `selection_decision_id` must be the one current active decision for the same Source and must equal:

```text
SELECT_FOR_REVIEW
```

A historical selection is insufficient.

`DEFER` and `REJECT_FOR_REVIEW` block new authorization.

### 3. Resolved license metadata

The Source must have:

```text
license.state = KNOWN
```

and a non-empty `declared_expression`.

A GitHub Search API license hint is not enough.

`UNKNOWN`, `CONFLICT`, `REVIEW_REQUIRED`, or `KNOWN` without an actual declared expression cannot authorize deeper acquisition.

### 4. Exact bounded scope

The authorization contains:

- one immutable revision;
- `selected-files` acquisition level;
- 1–32 explicit safe relative paths.

## Append-only authorization history

`source_acquisition_authorization` records use `aa:` IDs and are append-only.

A Source may have only one active authorization decision.

Changing the authorized scope requires a new `AUTHORIZE` record that explicitly supersedes the current active record.

The old authorization remains in history.

This avoids mutable permission objects whose historical meaning cannot be reconstructed.

## Revocation

Revocation is represented by another append-only authorization record:

```text
REVOKE
```

A REVOKE must supersede the currently active AUTHORIZE and copy its exact scope:

- Source;
- selection decision reference;
- acquisition level;
- revision;
- allowed paths.

The scope is repeated intentionally so the revocation identifies exactly what authority it cancels.

### Fail-safe revocation

REVOKE does **not** require the original selection to remain active and does **not** require the Source's license metadata to remain favorable.

This is intentional.

If new information changes the selection to `DEFER`, or licensing metadata becomes questionable, an operator must still be able to cancel an outstanding authorization immediately.

The safety rule is asymmetric:

```text
Granting authority requires all gates.
Removing authority must remain easy.
```

## No execution side effects

Creating either AUTHORIZE or REVOKE does not:

- mutate Source acquisition level;
- create a SourceSnapshot;
- create Evidence;
- fetch README;
- fetch source files;
- clone a repository;
- execute code;
- install dependencies;
- create Claims or Knowledge Entities.

`authorized_acquisition_requests` is a read view only. It is not an executor.

## Persistence

Migration `0006_source_acquisition_authorization.sql` creates normalized append-only storage with:

- Source foreign key;
- Source selection decision foreign key;
- decision constraint (`AUTHORIZE` / `REVOKE`);
- fixed `selected-files` acquisition level;
- explicit revision;
- JSON path allowlist limited to 1–32 entries;
- rationale;
- human actor provenance;
- one direct successor per old authorization.

`AuthorizationPostgresRepository` extends `SelectionPostgresRepository` and handles only the new `aa:` record family. Existing core record persistence remains untouched.

## CLI

Authorize an exact scope without retrieving it:

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

Read authorization state:

```bash
kneekura-acquisition-auth history --source-id src:github:owner:repo
kneekura-acquisition-auth active --source-id src:github:owner:repo
kneekura-acquisition-auth authorized
```

`authorized` displays active AUTHORIZE records paired with the current unchanged Source. It performs no retrieval.

## Security posture

Acquisition Authorization v1 is deliberately conservative:

- human-only;
- selected-files only;
- immutable GitHub commit SHA;
- maximum 32 exact paths;
- no traversal paths;
- active human selection required;
- resolved declared license required;
- append-only changes;
- explicit revocation;
- one active decision per Source;
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
- automatically select which files are useful;
- execute repository code.

## Next pressure

The next safe slice is **Authorized Acquisition Execution v1**.

That layer should consume exactly one active AUTHORIZE record, retrieve only its pinned revision and allowlisted paths, verify returned content against the requested revision/path, and record what actually happened separately from the authorization.

A safe execution record should make it possible to answer independently:

```text
Who selected this Source?
Who authorized acquisition?
What exact immutable scope was authorized?
Which files were actually retrieved?
What hashes did they have?
Did execution fully match the authorization?
```

Execution must never silently broaden an authorization when a requested file is missing or when repository layout changed.

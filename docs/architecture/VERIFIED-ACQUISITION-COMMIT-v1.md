# Verified Acquisition Commit v1

## Purpose

KNEEKURA TECH HUB now treats acquisition as five separate facts:

```text
found
  ≠ selected
  ≠ authorized
  ≠ fetched
  ≠ canonicalized
```

Authorized Acquisition Execution v1 proves only that a bounded set of files was fetched and verified at one point in time.

Verified Acquisition Commit v1 is the first gate that is allowed to change canonical Source provenance.

It consumes one successful acquisition execution and, only after independent re-verification, atomically creates:

- an immutable `SourceSnapshot`;
- the Source acquisition-depth transition `metadata-only → selected-files`;
- a `source_acquisition_commit` audit record;
- a `SOURCE_ACQUIRE` curation event.

It does **not** create Evidence, Claims, Knowledge Entities, or semantic recommendations.

## Why execution is not enough

Fetched files live in a private execution store. Between execution and canonicalization they may be:

- deleted;
- modified;
- replaced;
- supplemented with unauthorized files;
- replaced with symlinks;
- detached from the Source/Authorization state that existed during execution.

Therefore Commit v1 does not trust a successful execution record by itself.

It re-reads the bytes.

## Execution provenance fingerprints

Commit v1 introduces migration `0008_execution_provenance_fingerprints.sql`.

New acquisition executions record deterministic SHA-256 fingerprints of the complete preflight:

```text
Source record
Authorization record
```

Canonical JSON is:

```text
UTF-8 JSON
sort_keys = true
separators = (",", ":")
```

The resulting fields are:

```text
source_fingerprint_sha256
authorization_fingerprint_sha256
```

They are nullable in PostgreSQL for historical compatibility, but **Verified Commit refuses executions that do not contain both fingerprints**.

This means a legacy successful execution can remain valid history without silently becoming eligible for canonicalization under stronger rules.

## Store verification

Before any canonical write, Commit v1 requires:

1. execution exists and is `SUCCEEDED`;
2. execution schema and execution-history relationships validate;
3. execution contains both provenance fingerprints;
4. current Source fingerprint equals the execution-time Source fingerprint;
5. current Authorization fingerprint equals the execution-time Authorization fingerprint;
6. Authorization is currently effective;
7. Source is still `metadata-only`;
8. execution revision equals Authorization revision;
9. execution paths equal Authorization paths;
10. storage directory exists and is not a symlink;
11. actual file set equals requested path set exactly;
12. no unexpected directories exist;
13. no symlink or non-regular file exists anywhere in the store;
14. every file byte count matches;
15. every SHA-256 matches;
16. every Git blob SHA matches;
17. the execution manifest recomputes exactly.

Any mismatch rejects canonicalization without mutating Source state.

## Exact file-set semantics

The store may contain only the files explicitly authorized and the parent directories necessary to hold them.

Examples:

```text
Authorized:
README.md
src/lib.rs
```

Allowed directory structure:

```text
README.md
src/
  lib.rs
```

Rejected additions include:

```text
EXTRA.txt
cache/
unused-empty-directory/
```

This prevents execution storage from becoming an implicit directory-level acquisition authority.

## Symlink and special-file policy

v1 rejects symlinks anywhere below the execution store.

Files must be regular files. Directory entries must be real directories.

This prevents an authorized relative path from being redirected to material outside the verified execution store.

## Two verification passes

There are two storage verification passes.

### Pass 1 — preparation

Before building the Snapshot/commit records, the complete store is rehashed.

### Pass 2 — locked prewrite check

The PostgreSQL transaction then locks:

- the Source row;
- all Source Selection rows for that Source;
- all Acquisition Authorization rows for that Source;
- the target Execution row.

After these authority rows are locked, the store is re-read and rehashed again **before any canonical DB write**.

This closes the ordinary verify-then-commit race as far as the local storage model can.

The physical store is still not treated as self-authenticating truth. The canonical Snapshot stores content hashes and manifest identity; downstream consumers must verify bytes against that provenance when reading them.

## Atomic PostgreSQL commit

Migration `0009_verified_acquisition_commit.sql` adds the `source_acquisition_commit` record (`vc:` IDs).

The following mutations happen in one PostgreSQL transaction:

```text
INSERT SourceSnapshot
UPDATE Source acquisition_level → selected-files
INSERT source_acquisition_commit
INSERT SOURCE_ACQUIRE curation_event
```

If any statement fails, all four roll back.

The generic `put()` API is intentionally not allowed to create `source_acquisition_commit` records. Canonical commit must pass through the atomic repository path.

## Row-lock revalidation

Inside the transaction, after locks are acquired, Commit v1 rechecks:

- Source record is unchanged from preparation;
- Authorization record is unchanged;
- Execution record is unchanged;
- Source fingerprint still matches execution provenance;
- Authorization fingerprint still matches execution provenance;
- Authorization is still effective;
- Source is still metadata-only;
- Execution is still successful;
- no previous commit exists for the Execution.

Only then is the second store verification run.

## SourceSnapshot semantics

The created Snapshot uses:

```text
revision = exact execution revision
content_hash = execution manifest SHA-256
```

The metadata explicitly declares:

```text
content_hash_kind = selected-files-manifest-sha256
```

Therefore `content_hash` does not pretend to be a hash of a full repository tree.

Snapshot metadata records:

- acquisition level `selected-files`;
- execution ID;
- authorization ID;
- manifest SHA-256;
- execution storage key;
- exact selected-file results;
- execution-time Source fingerprint;
- execution-time Authorization fingerprint.

## Deterministic identity

The default Snapshot ID is deterministic from:

```text
Source ID
revision
manifest SHA-256
```

and uses the namespace:

```text
ss:acq:<sha256>
```

The default verified commit ID is deterministic from:

```text
Execution ID
Snapshot ID
```

and uses:

```text
vc:<sha256>
```

This makes accidental duplicate canonicalization easier to detect while PostgreSQL also enforces one commit per Execution.

## Authority after commit

Authorization effectiveness intentionally requires a metadata-only Source.

After a successful commit:

```text
Source.acquisition.level = selected-files
```

so the old Authorization becomes historical/non-effective automatically.

This prevents the same metadata-only acquisition grant from being reused as continuing authority after canonicalization.

## Execution store vs canonical truth

The execution store remains a material cache.

Canonical truth is the recorded combination of:

```text
SourceSnapshot
exact revision
exact selected-file list
per-file SHA-256
per-file Git blob SHA
manifest SHA-256
Source/Authorization provenance fingerprints
```

If stored bytes change later, they no longer match the canonical Snapshot and must be rejected by downstream verification.

## Audit event

The same transaction appends:

```text
operation = SOURCE_ACQUIRE
```

with subject IDs:

```text
Source
SourceSnapshot
Execution
Verified Commit
```

No Evidence is generated automatically.

Acquisition proof and semantic evidence remain separate concepts.

## CLI

Read-only verification:

```bash
kneekura-acquisition-commit verify ax:<execution-id> \
  --storage-root ./var/acquisitions
```

Successful output means only:

```text
VERIFIED_NOT_COMMITTED
```

Canonical commit:

```bash
kneekura-acquisition-commit commit ax:<execution-id> \
  --storage-root ./var/acquisitions \
  --actor-id acquisition-committer
```

Read commit history:

```bash
kneekura-acquisition-commit history
kneekura-acquisition-commit history --source-id src:<id>
kneekura-acquisition-commit history --execution-id ax:<id>
```

## Explicitly not included

Commit v1 does not:

- create Evidence;
- create StagedObservations;
- create Claims;
- create or merge Knowledge Entities;
- infer a license;
- execute acquired code;
- widen selected-file scope;
- clone a full repository;
- declare a Source useful, safe, performant, or recommended.

## Resulting pipeline

After this slice the acquisition path is:

```text
GitHub Discovery
      ↓
metadata-only Source
      ↓
Human Selection
      ↓
Human Authorization
      ↓
Bounded Machine Execution
      ↓
Independent Store Re-verification
      ↓
Atomic Verified Acquisition Commit
      ↓
selected-files Source + immutable SourceSnapshot
```

The next safe layer can begin **Evidence Extraction from Canonical Selected Files**, but extraction should still create StagedObservations / Evidence candidates rather than directly creating validated knowledge.

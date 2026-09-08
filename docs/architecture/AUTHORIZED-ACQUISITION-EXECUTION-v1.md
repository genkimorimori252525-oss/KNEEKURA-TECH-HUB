# Authorized Acquisition Execution v1

## Purpose

KNEEKURA TECH HUB deliberately separates four stages:

```text
Discovery
   ↓
metadata-only Source
   ↓
Human Selection
   ↓
Human Authorization
   ↓
Authorized Acquisition Execution
```

Execution v1 performs the network/file retrieval step, but **does not promote the result into canonical evidence**.

The next canonicalization step remains separate.

```text
Execution succeeded
      ≠
SourceSnapshot committed
```

## Core contract

Execution consumes exactly one currently-effective `AUTHORIZE` record.

It may retrieve only:

- the Source named by that authorization;
- the exact immutable revision named by that authorization;
- the exact ordered `allowed_paths` named by that authorization.

The executor cannot add paths, widen to a directory, switch revision, or convert selected-files authority into full-source authority.

## v1 provider scope

v1 fetches GitHub repository files through the GitHub Contents API.

The request is fixed to:

```text
/repos/{owner}/{repo}/contents/{authorized-path}?ref={40-hex-commit}
```

The authorization layer already requires a canonical lowercase 40-hex GitHub commit SHA.

The execution layer does not accept `main`, `master`, tags, abbreviated SHAs, or `latest`.

## Resource bounds

Execution is intentionally small:

- maximum 32 authorized paths;
- maximum 1 MiB decoded content per file;
- maximum 8 MiB decoded content per execution;
- maximum 2 MiB GitHub API response per request.

A limit violation fails the whole execution.

No partial result is published as a successful acquisition.

## File verification

For every fetched file, the executor records and verifies:

- exact authorized path;
- byte count;
- SHA-256 content digest;
- Git blob SHA-1 identity.

The Git blob identity is independently recomputed as:

```text
sha1("blob " + byte_length + NUL + content)
```

and must equal the provider-reported blob SHA.

Git SHA-1 here is an upstream Git object identity, not the Hub's security digest. The Hub also records SHA-256 for the content.

The GitHub response path, when present, must equal the authorized path.

Base64 is decoded strictly after removing permitted whitespace; arbitrary non-base64 garbage is rejected.

## All-or-nothing local publication

Files are first written below a private temporary directory inside the configured storage root.

```text
storage-root/
  .ax-<temporary>/
```

Only after every file passes verification and postflight authorization checks is the temporary directory atomically renamed into its execution store.

The final filesystem key is **not derived directly from user-controlled execution ID text**.

Instead:

```text
storage_key = "ax-" + sha256(execution_id)
```

This prevents an execution ID containing path separators or traversal text from influencing the filesystem destination.

If persistence of the successful execution record fails after the rename, the published directory is deleted again.

## Failure behavior

A single file failure fails the execution.

The execution record still covers the complete requested scope:

- files fetched before the failure remain marked `FETCHED` in the audit record;
- the failing path is marked `FAILED` with a concrete error code;
- later paths are marked `FAILED / NOT_ATTEMPTED_AFTER_FAILURE`.

Temporary file content is removed.

A failed execution has:

```text
manifest_sha256 = null
storage_key = null
```

so downstream code cannot mistake partial retrieval for a published acquisition.

## Preflight and postflight authority

Authority is checked before the first fetch and again after all files are fetched.

The postflight check catches:

- authorization supersession or revocation;
- Source no longer metadata-only;
- license no longer resolved;
- Source selection no longer current `SELECT_FOR_REVIEW`.

If authority becomes ineffective mid-execution, all fetched content is discarded and the result is recorded as:

```text
FAILED / AUTHORIZATION_BECAME_INEFFECTIVE
```

## Provenance race protection

In addition to ordinary authorization effectiveness, v1 snapshots the preflight Source and Authorization records in memory.

After retrieval it requires the current records to be structurally identical to those preflight records.

If the Source changes while retrieval is running:

```text
FAILED / SOURCE_CHANGED_DURING_EXECUTION
```

If the Authorization record itself changes:

```text
FAILED / AUTHORIZATION_CHANGED_DURING_EXECUTION
```

This prevents retrieved bytes from being attributed to provenance that changed during the operation.

## Execution authority

Creating Selection and Authorization decisions is human authority.

Executing an already-authorized bounded request is machine authority.

Therefore `executed_by.actor_type` is limited to:

```text
tool
system
```

A human/AI actor cannot be recorded as the executor in v1.

The Schema, validator, domain executor, and PostgreSQL migration all enforce this boundary.

## Execution record

A successful `source_acquisition_execution` (`ax:`) records:

```text
authorization_id
source_id
revision
requested_paths
status = SUCCEEDED
file_results[]
manifest_sha256
storage_key
executed_by
policy_version
executed_at
authorization_effective_after = true
```

A failed record records the same requested provenance plus an error code, but publishes no manifest/storage key.

Execution records are append-only.

Only one `SUCCEEDED` execution is permitted per Authorization.

## Manifest

The manifest SHA-256 covers deterministic JSON containing:

- authorization ID;
- Source ID;
- revision;
- ordered per-file path;
- byte count;
- SHA-256;
- Git blob SHA.

The manifest does not itself make the acquisition canonical. It is an integrity handle for the later commit gate.

## PostgreSQL constraints

Migration `0007_source_acquisition_execution.sql` enforces, among other things:

- `ax:` ID namespace;
- valid execution status;
- 1–32 requested paths;
- one file result for every requested path;
- tool/system executor only;
- safe hashed storage-key format;
- SUCCEEDED requires manifest/storage and effective postflight authority;
- FAILED forbids manifest/storage and requires an error code;
- at most one successful execution per Authorization.

The Python validator adds stronger per-file semantic checks and rejects malformed persisted records when history is read.

## CLI

Execute one current authorization:

```bash
kneekura-acquisition-exec execute aa:<id> \
  --storage-root ./var/acquisitions \
  --actor-id github-fetcher \
  --actor-version v1
```

Optional authentication is read from an environment variable rather than a CLI token value:

```bash
export KTHUB_GITHUB_TOKEN=...
kneekura-acquisition-exec execute aa:<id> \
  --storage-root ./var/acquisitions \
  --actor-id github-fetcher
```

A different environment-variable name may be selected with `--github-token-env`.

Show execution history without fetching:

```bash
kneekura-acquisition-exec history --authorization-id aa:<id>
kneekura-acquisition-exec history --source-id src:<id>
```

## Explicitly not included

Execution v1 does **not**:

- mutate `Source.acquisition.level`;
- create a `SourceSnapshot`;
- create Evidence;
- create a StagedObservation;
- create Claims or Knowledge Entities;
- execute downloaded code;
- clone full repositories;
- automatically widen authorization scope;
- treat successful retrieval as proof that a technology is useful or correct.

## Next gate

The next safe slice is **Verified Acquisition Commit v1**.

It should consume only a verified successful execution, re-hash the stored files against the execution manifest, confirm the Source/revision relationship, and then create the canonical `SourceSnapshot` / selected-files acquisition state under a separate explicit commit operation.

This keeps:

```text
found
≠ selected
≠ authorized
≠ fetched
≠ canonicalized
```

as separate auditable facts.

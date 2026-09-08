# GitHub Discovery Adapter v1

## Purpose

Controlled Discovery Intake v1 established a safe write boundary for large-scale discovery:

```text
untrusted discovery output
        ↓
Controlled Discovery Intake
        ↓
Source / SourceSnapshot / Evidence / NEW StagedObservation
        ↓
Curation Gate
        ↓
Canonical Knowledge
```

GitHub Discovery Adapter v1 adds the first upstream adapter for that boundary.

Its responsibility is deliberately narrow:

```text
GitHub Repository Search API
        ↓
GitHub Discovery Adapter
        ↓
metadata-only Controlled Discovery batch JSON
```

The adapter does **not** write PostgreSQL and does not call canonical curation operations.

To persist a generated batch, a separate command must pass it through the existing Controlled Discovery gate:

```text
kneekura-github-discover
        ↓ JSON
kneekura-hub discovery-check
        ↓
kneekura-hub discovery-ingest
```

This two-step architecture prevents a crawler bug from becoming a direct canonical-database write path.

## v1 output boundary

The adapter emits only `source` records.

Every generated Source is:

```yaml
record_type: source
kind: repository
acquisition:
  level: metadata-only
license:
  state: REVIEW_REQUIRED
  declared_expression: null
  handling_policy: DISCOVERY_METADATA_ONLY
```

The adapter does not create:

- SourceSnapshots;
- Evidence;
- StagedObservations;
- Knowledge Entities;
- Claims or Relations;
- Review Decisions;
- Curation Events.

Selected-file acquisition therefore cannot happen accidentally during repository search.

## Public OSS only

This adapter is for OSS discovery.

An authenticated GitHub token can expose repositories that are not public. v1 refuses to convert such results into Hub Sources.

A repository is skipped when:

- `private == true`;
- `visibility` is present and is not `public`;
- neither `visibility: public` nor `private: false` establishes public visibility.

Unknown visibility fails closed.

The generated batch records `skipped_nonpublic_count` as operation provenance without copying the skipped repository into the Hub.

## Deterministic identity

The adapter reuses the Controlled Discovery GitHub identity rule:

```text
owner/name
  ↓ lowercase
src:github:owner:name
```

Case variants in one search page collapse to one Source candidate.

The output records `duplicate_source_count`, while provider order for the first occurrence is retained.

## Search order is provenance, not quality

GitHub Search may return results in provider-defined order or with explicit API ordering such as:

- `stars`;
- `forks`;
- `help-wanted-issues`;
- `updated`.

KNEEKURA TECH HUB does not reinterpret that order as technological quality.

The adapter:

1. preserves the provider result order;
2. never sorts repositories itself by stars, forks, language, or other popularity metadata;
3. stores requested `api_sort` and `api_order` in the batch scope;
4. includes sort/order in the deterministic batch ID material.

Thus two searches with the same query and repositories but different ordering parameters remain distinguishable discovery events.

A repository with 7 stars can remain before one with 900,000 stars if that is the provider response order. Star count is metadata, not a Hub recommendation score.

## License metadata is only a hint

GitHub repository search results may contain a license object and `spdx_id`.

v1 stores that value under:

```text
source.origin.github_license_hint
```

It does **not** copy the hint into `license.declared_expression` and does not mark the Source license `KNOWN`.

All adapter-created Sources remain:

```text
license.state = REVIEW_REQUIRED
acquisition.level = metadata-only
```

A later, separately governed license/acquisition review must verify the actual repository material before any deeper acquisition can be allowed.

This prevents search metadata such as `MIT`, `NOASSERTION`, or stale provider detection from silently becoming a legal conclusion.

## Metadata retained

When present, the adapter may preserve descriptive GitHub search metadata such as:

- GitHub repository ID;
- node ID;
- default branch;
- description;
- primary language;
- fork/archive/disabled flags;
- visibility;
- star count;
- fork count;
- open issue count;
- pushed/updated timestamps;
- topics;
- GitHub license hint.

These values are discovery metadata only. They are not Facts about technical merit and are not Evidence for a Claim.

## Adapter batch provenance

Generated Controlled Discovery scope includes:

- query;
- page;
- API sort/order;
- adapter version marker;
- metadata-only/public-only flags;
- input item count;
- output Source count;
- case-duplicate count;
- skipped non-public count;
- GitHub API `total_count` when available;
- GitHub API `incomplete_results` when available.

The deterministic batch ID is derived from:

```text
query
page
sort/order
ordered Source IDs
```

The discovery timestamp is intentionally not part of the ID, so repeating the exact same search result set with the same search contract identifies the same logical batch content.

## One page per batch

v1 fetches or converts one repository-search page at a time.

Live GitHub search accepts at most 100 items per API page. Controlled Discovery itself permits up to 1000 records per transaction, but the Adapter does not automatically paginate across many pages in v1.

This is intentional. Multi-page scheduling introduces additional concerns:

- rate limits;
- partial-page failures;
- changing results during pagination;
- restart cursors;
- duplicate handling across pages;
- query-run identity.

Those belong in a later bounded discovery-run orchestrator rather than being hidden inside the first adapter.

## Live and offline modes

### Live GitHub API

```bash
kneekura-github-discover \
  --query 'incremental parsing language:Rust' \
  --output discovery.json
```

`GITHUB_TOKEN` is used when present. The token is sent only in the request Authorization header and is not written into the generated batch.

Optional provider ordering can be requested:

```bash
kneekura-github-discover \
  --query 'incremental parsing' \
  --sort updated \
  --order desc \
  --output discovery.json
```

The ordering is recorded as provenance and is not promoted into a quality score.

### Offline/reproducible conversion

```bash
kneekura-github-discover \
  --query 'incremental parsing' \
  --input-json github-search-response.json \
  --output discovery.json
```

CI uses offline fixtures so Adapter conversion tests do not depend on network availability, GitHub rate limits, or changing search results.

## Persistence remains separate

Adapter output should be checked and ingested through the established gate:

```bash
kneekura-hub discovery-check discovery.json

kneekura-hub discovery-ingest \
  discovery.json \
  --actor-type tool \
  --actor-id github-discovery-adapter \
  --actor-version 1.0
```

The actor supplied to `discovery-ingest` must match the batch `discovered_by` exactly.

The Adapter itself never imports or calls `PostgresRepository`.

## Security posture

GitHub Discovery Adapter v1:

- calls only the fixed `https://api.github.com/search/repositories` endpoint in live mode;
- does not clone repositories;
- does not execute repository code;
- does not install dependencies;
- does not download arbitrary repository files;
- does not create snapshots or Evidence;
- does not store authentication tokens in output;
- refuses non-public/unknown-visibility repositories;
- emits only metadata-only Sources;
- relies on Controlled Discovery preflight before output is considered writable intake.

## Verification fixture

The offline fixture deliberately contains:

1. a small repository with 7 stars returned first;
2. a repository with 900,000 stars returned second;
3. a case-variant duplicate of the second repository.

The acceptance contract verifies that:

- provider order is preserved;
- popularity does not reorder results;
- the logical duplicate is collapsed;
- all Sources remain metadata-only;
- GitHub license metadata remains a hint;
- output passes Controlled Discovery preflight.

Additional tests inject private, internal, and unknown-visibility repositories and confirm none are persisted as OSS Sources.

## Non-goals

v1 does not:

- automatically paginate a full GitHub search;
- schedule recurring crawls;
- rank technologies;
- infer technical quality from stars/forks;
- verify repository licenses;
- upgrade acquisition beyond metadata-only;
- fetch README/source files;
- create Evidence or observations;
- run semantic candidate extraction;
- create canonical knowledge;
- write directly to PostgreSQL.

## Next pressure

The next safe layer is a **bounded Discovery Run / Query Set orchestrator** or a **Metadata Review & Selection Gate**.

Either way, deeper acquisition must remain explicit. A search hit should never jump directly from GitHub metadata to selected-file acquisition merely because it is popular or matches a keyword.
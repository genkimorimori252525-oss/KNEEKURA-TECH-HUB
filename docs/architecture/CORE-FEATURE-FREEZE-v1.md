# KNEEKURA TECH HUB — Core Feature Freeze v1

Status: **FROZEN BASELINE**  
Baseline main commit before this declaration: `ec7a8fbf06e5d96c347cab26293a18bd4861a128`

## Decision

The core KNEEKURA TECH HUB architecture is considered complete enough for its original v1 purpose. Development does **not** continue by default merely because another feature can be imagined.

The default state after this document is **feature freeze**.

A new implementation slice should be opened only when at least one of the following is demonstrated:

1. a reproducible defect in an existing invariant or accepted workflow;
2. a required original-purpose workflow that cannot be completed with the current system;
3. a concrete operational failure observed during real use;
4. a security, privacy, integrity, license, provenance, or governance weakness with evidence;
5. an upstream/platform change that breaks an existing accepted path.

Convenience alone, speculative extensibility, possible future scale, or the existence of an interesting feature is not sufficient evidence to reopen the core.

## Original-purpose completion check

The Hub was designed to discover engineering knowledge broadly while separating discovery from trusted knowledge, preserving provenance, and preventing automated systems from silently turning guesses into canonical truth.

The current implementation has acceptance evidence for the following core chain:

```text
Discovery metadata
  -> Source
  -> human selection/license/authorization gates
  -> bounded acquisition execution
  -> verified acquisition commit
  -> immutable SourceSnapshot
  -> Evidence
  -> StagedObservation
  -> human canonicalization / Claim candidate
  -> human Support
  -> human Validation
  -> contextual retrieval
  -> provenance explanation
```

The following failure pressures have also been exercised:

- reviewed Claim and provenance immutability;
- append-only governance history;
- Source, Knowledge Entity, and StagedObservation identity integrity;
- cross-source evidence attachment;
- competing Claims without forced contradiction or winner selection;
- repeated upstream revisions without history rewriting or semantic resurrection;
- real commit-pinned upstream revision change;
- real cross-source design divergence;
- exact applicability-based contextual retrieval;
- explanation of contextual guidance back through Evidence, SourceSnapshot, and Source;
- a read-only external query surface that preserves ambiguity and fails closed on malformed context/provenance.

## Deliberately frozen-out features

The absence of the following is **not** currently a defect:

- natural-language Knowledge Entity search;
- semantic embeddings or fuzzy matching;
- recommendation ranking or a universal score;
- popularity or recency weighting;
- automatic contradiction inference;
- automatic winner / preferred Claim selection;
- automatic entity merge;
- automatic Claim validation or terminal disposition;
- automatic context inference;
- mass crawling enabled by default;
- HTTP/API server solely for convenience;
- new canonical tables that duplicate existing provenance or projections;
- taxonomy expansion without a demonstrated use case.

These remain possible future products or operational layers, not unfinished core architecture.

## Preservation rule for future work

When a new pressure appears, prefer this order:

```text
1. reproduce the failure
2. prove which existing invariant/workflow is insufficient
3. test the narrowest repair
4. change the fewest production surfaces
5. preserve existing provenance and authority boundaries
6. stop again when the proved defect is gone
```

A test-only PR that proves the existing implementation already handles a pressure is a successful result. It is not a reason to invent additional machinery.

## Known maintenance signals that do not reopen the core today

GitHub Actions currently emits a Node.js 20 deprecation warning for `actions/checkout@v4` and `actions/setup-python@v5` while the runner forces Node.js 24. Existing CI remains green. Treat this as platform maintenance when it becomes actionable, not as a reason to expand Hub architecture.

## Reopen rule

Any proposal to reopen the frozen core should state, before implementation:

- the observed failure or unmet original-purpose workflow;
- exact reproduction evidence;
- the invariant affected;
- why an existing surface cannot satisfy it;
- the smallest proposed change;
- explicit non-goals.

If those cannot be stated concretely, the correct action is **do not add the feature**.

## Final v1 posture

The Hub should now be treated as a preservation-first, evidence-driven usable core rather than an endlessly growing design exercise.

> Preserve what works. Repair what is proven broken. Do not manufacture work to keep development moving.

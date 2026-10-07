# KNEEKURA Deliverables

This directory contains **downstream products built with knowledge from KNEEKURA TECH HUB**.

It exists to prevent a research repository from slowly turning into the source tree of one product.

## Boundary

`departments/` answers:
- What technology exists?
- How does it work?
- What evidence supports the finding?
- What failed upstream and how was it repaired?
- How can the technique be ported?

`deliverables/` answers:
- What are we building with that knowledge?
- What is the current product source?
- Which researched techniques were actually adopted?
- What happened during our own development?
- What was built/tested/released?

A deliverable may link to research. It must not become the canonical home of upstream analysis.

## Required shape

Every long-lived deliverable uses:

```
deliverables/<domain>/<deliverable-id>/
├─ README.md       # identity, purpose, navigation
├─ STATUS.md       # current truth and next action
├─ ADOPTION.md     # research -> product decisions
├─ mod|app|tool/   # actual product source
├─ history/        # decisions, timeline, own failures/repairs
└─ evidence/       # small derived verification manifests/receipts
```

Optional `release/` may contain release notes/manifests, not large binaries.

## Permanent operating rules

1. **Research remains upstream.** Do not move `departments/*` analysis into a deliverable merely because the product uses it.
2. **No raw third-party source dumps.** Full upstream checkouts/JARs/decompiled trees stay in the established analysis/cache workflow.
3. **Adoption is explicit.** A researched technique enters product design through `ADOPTION.md` with source locator, license/provenance note, adaptation decision and status.
4. **Product code owns only KNEEKURA implementation.** Third-party code is copied only after an explicit license/compliance decision; technique reimplementation is preferred when practical.
5. **Own failures are first-class history.** Regressions, wrong assumptions and repairs go under `history/`, using the Minecraft Failure/Repair format when applicable.
6. **Evidence is bounded.** Git stores small manifests, hashes, summaries and receipts. Raw worlds, videos, large captures, credentials and private runtime artifacts remain outside normal Git.
7. **Status is not inferred from old plans.** `STATUS.md` is the entry point for another AI. Historical plans remain historical.
8. **No silent promotion.** A successful build is not gameplay acceptance; a screenshot is not behavior parity; a research candidate is not a product requirement.
9. **Archive rather than erase.** Superseded product decisions remain in history. The current document points to their replacement.
10. **One deliverable does not redefine the Hub.** Root README, department queues and canonical knowledge governance remain independent of any product.

## Lifecycle

- `PROTOTYPE`: architecture/source is actively forming.
- `ACTIVE`: product implementation and verification are ongoing.
- `FROZEN`: accepted product is intentionally stable; only defects/requirements reopen it.
- `ARCHIVED`: retained for history, not an active target.

The lifecycle describes the deliverable only. It does not change the status of research departments or canonical knowledge.

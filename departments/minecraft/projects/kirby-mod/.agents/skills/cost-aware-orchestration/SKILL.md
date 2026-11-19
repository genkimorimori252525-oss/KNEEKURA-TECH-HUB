---
name: cost-aware-orchestration
description: Route non-trivial repository tasks by complexity, risk, evidence, and model cost. Use for multi-module changes, broad investigation, debugging after a focused failed hypothesis, high-risk changes, implementation planning, review, or deciding whether to delegate. Do not use for a clearly scoped direct edit or a one-command lookup.
---

# Cost-Aware Orchestration

Use the least expensive route that preserves the task's required quality. The parent remains the only default writer and verifies source evidence before editing.

## 1. Classify before delegating

Assign both values before selecting a route.

- Complexity: `S` for one clear local change, `M` for bounded multi-file work, `L` for cross-module or ambiguous work.
- Risk: `R0` for reversible local changes, `R1` for compatibility or behavior-sensitive changes, `R2` for data, migrations, authentication, authorization, secrets, concurrency, public APIs, or irreversible external actions.

| Class | Route |
| --- | --- |
| `S/R0` | Parent inspects, edits, and runs targeted verification directly. |
| `M/R0` | Delegate to `scout` only when the investigation is independent and bounded. |
| `L/R0` or `R1` | Gather evidence, then use `expert` in `PLAN` mode if a design decision remains. |
| Any `R2` | Use an evidence-backed Expert plan or review, define rollback or reversibility, and require strict verification. |

Do not delegate merely because a task is unfamiliar, a first test failed, or a second opinion would be pleasant.

## 2. Apply the delegation break-even check

Delegate to `scout` only when all conditions hold:

1. The question is independent of current implementation work.
2. The scope and expected output can be stated precisely.
3. The parent will not need to repeat the same repository search.
4. Parallelism or output compression offsets the extra prompt and summary cost.

Use the parent directly for a one-command lookup, one symbol search, or a small error excerpt. Use Terra-level investigation instead of Luna when broad relevance judgment is required.

## 3. Keep handoffs evidence-first

Give Scout or Expert only a compact brief:

```text
Objective:
Complexity / risk:
Target commit or working-tree state:
Relevant files and symbols:
Confirmed facts:
Rejected hypotheses:
Minimal error or test signature:
Constraints and invariants:
One question to answer:
```

Do not send full logs, full source files, or an unfiltered conversation. Treat returned summaries as an index; before editing, the parent reopens the cited source locations.

## 4. Use Expert as a soft budget

Use `expert` in exactly one mode per call:

- `PLAN`: choose an implementation approach, invariants, validations, risks, and open decisions.
- `CONSULT`: resolve one evidence-backed technical contradiction or judgment.
- `REVIEW`: inspect requirements, invariants, diff risks, and verification gaps without editing.

For ordinary work, allow one Expert call. Allow one additional call only when new evidence changes the question. Exceed this soft budget for `R2` safety work when the parent records the reason.

## 5. Use structured exits

Return one status: `DONE`, `NEEDS_MORE_EVIDENCE`, `NEEDS_REPLAN`, `NEEDS_USER_DECISION`, `BLOCKED_ENVIRONMENT`, `FAILED_VERIFICATION`, or `STOPPED_BUDGET`.

Every non-parent agent returns:

```text
STATUS:
Question or mode:
Evidence references:
Confirmed facts:
Unresolved items or risks:
Recommended parent action:
```

Only the parent asks the user a question. For `NEEDS_USER_DECISION`, provide concise options, their effects, and a recommendation.

## 6. Verify before reviewing

Run the narrowest relevant mechanical checks first: reproduction test, targeted test, type check, build, lint, and diff review. Request model review only when risk remains, evidence conflicts, or the task is `R2`.

Keep `context-mode` for large-output processing. Never index or persist secrets, credentials, or raw sensitive logs. Do not use `superpowers` orchestration during this trial.

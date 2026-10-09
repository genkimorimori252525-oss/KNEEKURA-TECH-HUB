# Project Instructions

- When adding or changing Kirby behavior, update `/tlm` debug output when the new behavior needs observability.
- `/tlm` should cover state lines, `thought=` lines, warning lines, held mob diagnostics, and relevant AI goal internals.
- When adding a new Kirby behavior concept or state transition, verify that it can be observed through `/tlm` or intentionally document why it does not need telemetry.
- When a playable mod jar is built, deploy the final mod jar to both:
  - `C:\Users\genki\AppData\Roaming\.minecraft\mods`
  - `C:\Users\genki\Downloads\Kirby_mod\Kirby\u5236\u4f5c\u904e\u7a0b\u30dc\u30c3\u30af\u30b9`
- The second deployment path uses Unicode escapes for portability. Decode it before copying; it is the existing Japanese-named directory under the project root.
- If deployment writes outside the workspace sandbox, request approval instead of silently skipping the copy.

# Cost-Aware Multi-Agent Trial

- The parent agent is the only default writer and integrator.
- Use `scout` only for independent, bounded, read-heavy work when delegation costs less than direct inspection.
- Use `expert` only in one explicit mode: `PLAN`, `CONSULT`, or `REVIEW`, with a compressed evidence brief and one decision question.
- Classify non-trivial work by complexity (`S`/`M`/`L`) and risk (`R0`/`R1`/`R2`) before delegation.
- Treat Sol as a soft budget: normally one Expert call, with another only for new evidence or `R2` risk.
- Prefer tests, type checks, builds, lint, and diff review before model review.
- Scout and Expert return structured statuses to the parent; only the parent asks the user questions.
- Do not use `superpowers` orchestration during this trial. Keep `context-mode` for large-output handling, but do not index secrets or credentials.

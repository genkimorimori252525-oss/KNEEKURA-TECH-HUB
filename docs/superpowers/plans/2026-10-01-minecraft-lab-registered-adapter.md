# Registered LAB Adapter and Resume Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Goal:** Complete the source-only local bridge and retained-evidence resume surface while real runtime acceptance is deferred.

**Architecture:** An explicit registry pins the Node executable, LAB entrypoint/import closure and private owner configuration. TECH HUB invokes only fixed bounded file operations through the existing synchronous process helper. LAB keeps its existing registration and action journals; TECH HUB retains sanitized receipts in its existing CAS. TaskContext reads retained reports and never starts a process.

**Tech Stack:** Python 3.11+, Node ESM built-ins, existing Store/process helper and LAB bridge.

**Spec:** `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md`, sections 16–17 and X7. Existing approved design and latest direction prioritize source implementation; live repair acceptance remains NOT_RUN.

## Global Constraints

- No daemon, network bridge, arbitrary request executable or second run owner
- Explicit private registry; exact pinned module closure; bounded input/output and deadline
- Unknown completion remains UNKNOWN; inspect/reconcile never dispatches or retries mutation
- Disk identity is not proof of JVM loaded bytes; registration is not runtime authority
- Keep raw logs/private paths out of public CAS summaries
- No new game process or live action for this task

## Review Focus

- Node options/import injection, changed executable/module/config and symlink/FIFO inputs fail closed
- Same request registration is idempotent only for identical hashes; incomplete registration is not silently repaired
- Timed-out local registration is UNKNOWN and is reconciled through existing LAB records
- Retained report linkage/current target drift cannot become current runtime evidence
- TaskContext does no subprocess, file write or mutation and never treats fixture evidence as live PASS

## Task 1: Fixed LAB adapter

- [ ] Add failing Node tests for strict owner config/input, register/inspect/reconcile operations and missing/tampered paths
- [ ] Implement `debug-workspace/bridge/adapter.mjs` and bounded `adapter-cli.mjs`, reusing registration/action-journal readers
- [ ] Reject unsupported execute/start/reset operations; return sanitized identity/readiness only
- [ ] Run all bridge tests and source aggregate

## Task 2: TECH HUB registered invocation

- [ ] Add failing tests for exact registry/module/executable checks, fixed operations, bounded timeout/output and redacted receipts
- [ ] Implement `experiment_adapter.py`: read-only `inspect_registry`, explicit `register_request`, read-only process `inspect_registration` and `reconcile_action`
- [ ] Materialize canonical retained request/assertion/binding/material bytes under an exclusive owner input directory, preserving raw hashes
- [ ] Add explicit CLI operations, no generic execute route
- [ ] Verify actual Node fixture roundtrip with no Minecraft process

## Task 3: Retained resume and TaskContext

- [ ] Add failing tests for second-agent report resume, UNKNOWN inspection and stale target handling
- [ ] Implement bounded `resume_experiment` in existing bridge: exact request/result hashes, assertions, unresolved issues and drill-down pointers, no arbitrary prose promotion
- [ ] Add experiment report/registry inputs to TaskContext, advertise implemented read-only surface while execution remains explicitly blocked/unattested
- [ ] Route uncertain report to `experiment.reconcile_unknown` and suppress new side-effecting advice
- [ ] Run focused, whole repository, and exact-head hosted source checks; independent review before publication

## Deferred acceptance

Actual loaded-JVM attestation, operator configured disposable-world grant, full MOD repair loop and visual benchmark are runtime gates and remain NOT_RUN. Their absence never converts a source test into real gameplay acceptance. X8 remains conditionally deferred until an actual X3 defect justifies it.

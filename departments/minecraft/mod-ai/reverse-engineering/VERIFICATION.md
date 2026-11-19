# Verification — 2026-10-17

## Observed in this implementation session

Base main: `e5149661a696cded69f6f7dd6db9bfbdeea06337`.
The local owner-PC connector was offline. Work used an isolated local changeset;
this is not a claim of inspecting that PC's uncommitted files or installing tools there.

```text
python -m unittest discover -s departments/minecraft/mod-ai/reverse-engineering/tests -p "test_*.py" -v
```

- Initial RED: 21 assertions failed because the opt-in implementation did not exist.
- Implementation GREEN: 21 passed.
- Expanded source contracts: **27 passed**, including REA local installation,
  exact version admission, argv forwarding, Windows npm.cmd-to-JS translation,
  and preserving unrelated local npm definitions.
- These are source contracts with mocked external processes/downloads, not
  executions of CFR, Vineflower, npm, REA, or a Windows runtime.
- Python syntax compilation and optional-suite pytest are separate final gates.
  Their results are included in the PR report, not assumed here.

## Structural review

No existing source, common dependency file, main CLI, startup hook, task
prepare/capabilities implementation, or existing Vineflower provider is changed.
All product additions live in the scoped shelf. One optional parent pointer and
one path-filtered CI workflow are added. Root AGENTS/skills/MCP are not added.

The contracts check no subprocess/network use at import/help/catalog, selected
installation only, missing/corrupt tool refusal, no existing evidence overwrite,
space-safe argument arrays, checksums, copied inputs, explicit classpaths, and
failure/timeout/empty-output receipts. Config generation preserves the existing
Vineflower provider interface without launching it.

## Not established by the source tests

Actual Java decompilation/recompilation, REA npm lifecycle-disabled package
usability, native Ghidra/JADX/IDA/etc integration, Windows execution, owner-PC
installation, full-repository regression, arbitrary game or source equivalence.
Do not turn a green contract suite into any of these claims.

The manual Actions job `real_tools=true` runs `smoke.py` on a small authored
Java17 fixture and REA version/help only. It publishes a bounded summary only
after all checks succeed. Consult the exact Actions run before claiming that
this job was executed; merely adding the workflow is not a pass.

## Known limits, not hidden guarantees

CFR's current checksum source is its official legacy MD5, not a strong signed
release or SHA-256 pin. Observed SHA-256 is recorded separately. REA's direct
version is pinned; its first install resolves transitive npm dependencies and
records the local package-lock. No global MCP or agent setting is modified.
This wrapper is not an OS sandbox, full package audit or disk-quota enforcer.

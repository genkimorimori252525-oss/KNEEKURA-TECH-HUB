# Hosted verification ledger — 2026-09-28

These are observed executions, not planned results. New runs remain visible in PR #73 checks; this document preserves the exact historical checkpoints below. GitHub-hosted ubuntu-latest only. No self-hosted runner was dispatched, no user world changed, no prior PR merged.

## Full repository / actual PostgreSQL

Initial hosted baseline:
- Head `ebc2c56af0b8aabb88a51d4470b75d6913300318`.
- Actions run 36375335442, job108779901684.
- 471 passed, 8 warnings; 0 failed/skipped.

Connected adapters:
- Head `2d6bd068c2f256c7789e994e43852ac55d2de39d`.
- Tested PR merge ref `2cb632f3277504a306af5b9c90d7920b1716dc3b` (ephemeral test merge, not a repository merge).
- [Actions run36377694140](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36377694140), job108786798219.
- `python -m pytest -q --junitxml=test-evidence/junit.xml`: **567 passed, 8 warnings, no failures/skips**.
- Python3.12.14 / pytest8.4.2 / Temurin17.0.20.1 / PostgreSQL16.15; declared Python dependency range installed.
- 8 warnings originate in existing Twilight runtime documentation strings with invalid escape sequences, not test failures. Negative PostgreSQL constraint tests emitted expected error log lines.
- Artifact10952006020, sha256 `9a450bc432a4d766899031aa2e47d3def2b053aa88f8664da66391bdbdd9133b`.

## Actual Forge compile and resolved input pipeline

Compile-only checkpoint:
- Head `c59f5f7905bf3a78f45e367282b470858c9a3c20`.
- Run36375956807/job108781716910, actual compileJava/jar/reobfJar PASS.
- Artifact10950688738, sha256 `a2ae01093bdef656925fbd736b2d4ed41b839857539ba4898154b4f0c5f8f774`.

Connected reference pipeline:
- Head `1cc570baf68ee94b7848639bfc595fc0ec96ebfa`.
- [Actions run36377840477](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36377840477), job108787219387.
- Official Minecraft1.20.1/Forge47.4.6 MDK, SHA1 checked against `1a1c045f235262ff617e285ea2156571ea93bfbe`; SHA256 retained in artifact.
- Gradle8.8 / Java17. Actual Forge/Minecraft dependencies downloaded and transformed by the MDK.
- `compileJava jar`: PASS, including reobfJar. ResourceLocation constructor deprecation warning remains; no compiler error.
- `kneekuraExportInputs` through our init script: PASS.
- `import_resolved` → `capture_profile` → `prepare_index` → `search` → full source read: PASS.
- 205 scoped resolved artifact entries, 37,933 captured documents. Scope duplicates/partial coverage are not hidden.
- Artifact10951627925, sha256 `cf51a2488bf60cf904c4f985235f966d17149c3e7cc906dcb9a5850e719be5d3`.

Only bounded logs, input hashes and verification summaries were uploaded as CI evidence. Minecraft binaries/full generated sources, CAS contents, private session secrets and user save data were not uploaded by these workflows. Artifact retention is seven days; the commit-pinned workflow and this ledger remain in the repository.

## Not established by these runs

No actual Minecraft/GameTest/client process was launched. No rendering, runtime behavior, MOD compatibility, performance or actual Vineflower/tiny-remapper execution has been established. Existing Core/PostgreSQL test success is not blanket proof of the new Core bridge against production data. Research-history fixtures do not establish any real upstream bug cause.

# M2 writer candidate — hosted verification, 2026-09-28

Status: **CANDIDATE FULL-SUITE PASS; INTEGRATION HOLD REMAINS**.
See [concurrent-change reconciliation](CONCURRENT-GUARD-HOLD-2026-09-28.md).
This is fresh evidence for the isolated candidate, not for the current PR #74
branch, a combination of both guards, or a live Blockbench/Minecraft execution.

## Exact execution

- Tested commit: `796f738a3f77be25404c77fd147ce85131bd78db`.
- Tested tree: `e19003c5b28fa10176d557b1f1e7723653ea97f6`.
- Branch: `jolly/minecraft-mod-ai-sealed-writer-2026-09-28`.
- [Run 36396533103](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36396533103), job `108844144324`, attempt 1.
- Automatic `push` event using unchanged `.github/workflows/test.yml`.
- GitHub-hosted Ubuntu, Python 3.12, Java 17, PostgreSQL 16 service with
  `KTHUB_TEST_DATABASE_URL` configured.
- Complete repository command: `python -m pytest -q --junitxml=test-evidence/junit.xml`.
- **814 passed, 0 failed, 0 errors, 0 skipped; 8 pre-existing invalid-escape warnings**.
- JUnit contains 814 actual testcases; the new Node guard suite is nested in one
  pytest case and is not added again to this total.

## Downloaded and checked evidence

Artifact `10957669798`, name
`hub-tests-796f738a3f77be25404c77fd147ce85131bd78db`, was downloaded.
Its ZIP SHA-256 equals the GitHub artifact digest:
`5553a48cdffcce734394fa1721540c9621749837b2d2f5ef6fe5fa97c3028c43`.

The archive has `commit.txt`, `dependencies.txt`, `junit.xml`, `pytest.txt`.
`commit.txt` matches the tested commit above. JUnit counts and the captured pytest
summary agree. Individual SHA-256 values:

- `commit.txt`: `e7f55ace1ce1fb1972b0a7f60fbbfd57ee609173e776c2c75523579e9edbf7f0`
- `dependencies.txt`: `5d116c6edee80f28cc10071c74f3464e0b81578925e02899ca74c59b2bd4e941`
- `junit.xml`: `c276f059fe7fc878520b66e090b94fdfbc85fc26ab7a1f783f4e50fdd01209f8`
- `pytest.txt`: `4119c07f190b3c8007f49b5a5aa2ecbdc03675fcd2525b4fdbfa58a5c5bbd691`

The original 88-case local result remains selected-file evidence. This hosted
run resolves full-repository testing only for the candidate's exact tree.
Later documentation-only commits do not change the tested executable revision.

## Unchanged limits and resume

No manual workflow dispatch, home runner, parent branch update, force push, PR
merge, plugin installation or production-world operation was performed.
Full pinned-source composition, loading the derivative into a disposable editor,
real multiview screenshots, native-file reopen, visual quality, Windows and real
Minecraft asset use remain NOT_RUN. The integration hold is not lifted by a
green test suite: first consolidate with the concurrent `asset_guard.py` work
and its pathless-capture changes, then run the combined suite and live acceptance.

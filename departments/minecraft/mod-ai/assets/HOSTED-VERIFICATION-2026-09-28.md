# Hosted verification — MOD-AI asset preflight, 2026-09-28

Status: **FULL REPOSITORY REGRESSION PASS**. This is not live asset/game acceptance.

- PR: #74, stacked on #73; no actual repository merge.
- Implemented/tested head: `5342df00c82c72a259d7ce971ae254e0a9bc2952`.
- GitHub synthetic PR test merge: `8ee124c9aec2b3dcdd434b1358818b8cf3176538`.
- Both use tree `130d47818c9714a8736b241b3c248e5d68014b94`; parents are the exact #73 baseline and this implementation commit.
- Workflow run: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36387017840
- Job: `108814421643` (`pytest`); workflow completed successfully.
- Environment: existing `test.yml`, standard GitHub-hosted ubuntu-latest, Python 3.12, Java 17, PostgreSQL 16 service configured through `KTHUB_TEST_DATABASE_URL`.
- Observed result: **726 passed / 0 failures / 0 errors / 0 skipped**; 8 existing invalid-escape warnings in Twilight Forest runtime helper. Test execution took 65.77 seconds.
- 597 existing tests plus 129 new asset/preflight/CLI tests; not an inferred count — downloaded JUnit and pytest log were parsed/checked.

## Artifact verification

Artifact `10954793023`, `hub-tests-8ee124c9aec2b3dcdd434b1358818b8cf3176538`, was downloaded. ZIP SHA-256:
`ceabafc80e2acd11b272c44ef5d2f1fb2ecf09d33100300fe46c555f4172a362`.

JUnit SHA-256: `a6f81337c01891d448ea7bfbba15f07dd7951b118da0ce2b0b437c2f36b3ab41`.
`commit.txt` equals the synthetic PR merge above. The synthetic merge's Git tree
was read back through the GitHub API and matches the implemented head exactly.
The artifact contains commit.txt, dependencies.txt, junit.xml and pytest.txt.
GitHub retention currently expires 2026-10-05; do not assume future availability.

All 14 uploaded files were read back by blob ID and matched the selected local
checkout. The code/tests are exactly the bytes recorded in [verification.json](verification.json).
The older 159-test selected-file proof and 597-test parent proof remain historical;
this hosted result adds whole-repository and configured PostgreSQL coverage.

## Scope boundary and resume

This follow-up adds this evidence document only, with skip-CI. It does not change
tested executable bytes or pretend its later documentation commit was the test head.
No pipeline configuration, home runner, visibility, parent branch or production
world changed. Automatic standard CI ran on the child PR; no manual dispatch.

M1 is verified at the implementation scope. Blockbench desktop/model export,
visual review, live Minecraft/client input, Windows, network/performance and the
existing real external-provider/Core caller acceptance are still NOT_RUN or pending.
Do not convert these Python/protocol regression tests into an asset or game PASS.
Continue at M2 in the [unified plan](../../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md).

# Hosted verification — M2 guarded Blockbench preparation, 2026-09-28

Status: **FULL REPOSITORY REGRESSION PASS FOR THE GUARDED-PREPARATION SLICE.**
This is not live Blockbench desktop, model-generation, export, visual-quality, Minecraft,
Windows-input, network, or performance acceptance.

- PR: #74, additive child of #73; no main or parent-PR merge.
- Tested PR head: `f0194b55c51ea8c1af651673c985bb4a82ace398`.
- GitHub synthetic pull-request merge: `f4a7938fe210e2989845779490dd086f29fbe7c8`.
- Workflow run: `36395198629` (`test`), completed successfully.
- Observed pytest result: **777 passed / 0 failures / 0 errors / 0 skipped** in 57.39s.
- Warnings: 8 pre-existing invalid-escape warnings in the Twilight Forest runtime helper.
- Artifact: `10957868221`, `hub-tests-f4a7938fe210e2989845779490dd086f29fbe7c8`.
- Artifact ZIP SHA-256: `5ea2d07498147ae5be156cbc135d45efb8cdd22f025753c288f7249e90e177d9`.
- JUnit SHA-256: `38a6f81e27301be76b5eb3497894dc03dd488e515fdb7c8c7d708032a28104af`.
- pytest log SHA-256: `069e0663eea73d38160bfe0d06386dc18c28d3b474f61d3edeed6ffb4ab2dd5a`.
- `commit.txt` SHA-256: `34b252ccd49bbde080aacebe4f8f53d73e47203508f0264d9e3902b7e0bde9c3`;
  its content is the synthetic merge SHA above.
- GitHub reports artifact expiry at 2026-10-05; future availability is not assumed.

## What this proves

The repository-wide automated suite accepts the published M2 guard-preparation changes,
including the M1 regressions and the fake-editor guard contract. It also proves that the
published branch bytes—not only the earlier local patch—fit the existing repository test
surface at this revision.

## What this does not prove

The Node guard suite uses the real guard implementation against a fake editor host. It does
not establish that the guarded derivative loads in Blockbench, that the selected plugin bytes
are the bytes currently loaded in an editor, that a Celestial Staff can be rendered/exported,
or that Minecraft can consume the result. Those remain explicit M2/M3 acceptance work.

Next: keep filesystem-path export blocked, add a bounded no-path capture boundary for model,
texture, and required-view evidence, then exercise that boundary in a disposable desktop
before enabling final native/export capture.

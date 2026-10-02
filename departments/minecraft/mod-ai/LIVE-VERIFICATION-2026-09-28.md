# Real Forge / GameTest / observation checkpoint — 2026-09-28

**Server integration slice: verified. Whole MOD-making AI environment: still IN_PROGRESS.**

Verified executable commit: `3fa14453327e7992231e3d479ac1d1eebbd96b3c` on PR #73. The follow-up documentation commit does not change executable code and uses `[skip ci]` to avoid launching the same game again for a prose-only update. No PR/main merge or repository-visibility change was performed.

## Actual successful run

[Live Actions run 36381518610](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36381518610), job `108798075071`, ran the actual Minecraft 1.20.1 / Forge 47.4.6 / Java 17 server on GitHub-hosted Linux. It did not use API stubs or the home self-hosted runner.

The existing production adapters performed:

1. Build a disposable probe MOD against the official MDK and record its compiled-class receipt.
2. Execute ForgeGradle's resolved-input export, import/capture the real dependencies and sources, and search the probe source.
3. Copy an explicitly registered empty template into a managed fresh run directory, prepare an exact build/source/world/scenario contract, and launch with the separate observer source set.
4. Authenticate over loopback and verify the expected session, target class-resource bytes, world path and seed. Post-Mixin in-memory instruction identity is not attested.
5. Execute registered commands, including a successful command whose numerical return value is zero. Submit the same scoreboard increment twice: the score remains **1**, and duplicate receipts are identical. Submit the same summon twice: its receipts are also identical.
6. Observe the exact summoned entity UUID in `minecraft:overworld`, using the existing UUID filter with a result limit of one. The returned pig has health 10 and a finite position/velocity; the selected result is not truncated. This is not a count of all pigs in the generated world.
7. Reject an incorrect authentication token, then release the game-side assertion and collect the authenticated same-run completion report.

The driver ended with `build PASS`, `export PASS`, `gametest PASS`, and `REAL_FORGE_LIVE_BRIDGE_AND_GAMETEST_PASS_WITH_PRESERVED_NEGATIVE_CONTROL`.

### GameTest outcomes: one pass and one deliberately retained failure

| Exact test ID | Required | Result | Interpretation |
|---|---|---|---|
| `bridge` | true | PASS | Game-side assertion saw the finish block and a scoreboard increment of exactly one. |
| `knownbad` | false | FAIL | Deliberate negative control. The failure must remain present and separate from the selected target. |

There were exactly **2 detected and 2 executed tests**, with a completed report. The oracle selected `bridge` as the required target and retained `knownbad` in unrelated failures. Do not describe this as two passing GameTests. The game's aggregate log wording is not used in place of exact per-test IDs, flags and results.

### Evidence identities

- Code commit: `3fa14453327e7992231e3d479ac1d1eebbd96b3c`.
- Live session run ID: `6d144fbf-0872-4ebe-bf8f-322447c692dd`.
- Index snapshot: `eaa6b255b840958903be53458386749ee4ab12c500e3cfaeb2b78469f48004fd`.
- Profile: `f146fe7f0a2c934ee41db8e280c3a0c6e03e39611a0022d44ce3bb32e12929da`.
- Live artifact ID: `10953495169`; SHA-256 `fa704bdbd8a92bb0f73dbd3f156b83ae33f899c38065c0154f540836e56b5994`.
- Artifact includes bounded build/export/game logs, decoded non-secret handshake and entity observation, eight command-response records including duplicates, GameTest report and summary. It excludes session secrets, full CAS, generated Minecraft sources and world saves.
- The downloaded ZIP digest, commit file, individual command receipts, entity record, driver output and test report were checked after the workflow completed. Seven-day CI artifact retention is not permanent evidence storage; a compact summary remains in [verification/live-2026-09-28.json](verification/live-2026-09-28.json).

The reporter's `exit_code` field is a placeholder with an explicit completion-semantics note. The production execution adapter supplies the actual process exit when evaluating results. Do not infer process success from the reporter's placeholder alone.

## Complete repository regression suite

[Actions run 36381522497](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36381522497): **597 passed, 0 failed, 0 errors, 0 skipped, 8 existing warnings**. Python 3.12, declared pytest 8 dependency range, Java 17 and configured PostgreSQL 16 were used.

- PR head: `3fa14453327e7992231e3d479ac1d1eebbd96b3c`.
- Tested synthetic PR merge: `675385657caa0dbb66e71605813f556651d8d5a3`. This is an ephemeral CI test ref, not a merge of PR #73.
- Artifact `10952439050`; SHA-256 `ab2076a353a8923a94a67628d399dac5f9ea2d34f189c9280c822786da021c73`.
- JUnit XML and commit file were downloaded and checked. Eight warnings concern pre-existing invalid escapes in Twilight runtime Python strings; they are not failing tests.

The new command and fixture checks total 14 cases beyond the earlier 583-case checkpoint. This library test count is distinct from the two actual GameTests above.

## Failures investigated rather than hidden

### 1. Producer/consumer command contract

Before commit `400838443cd35a491acf8a9395f96a550cce608a`, Java emitted `success`, while the Python result oracle expected `outcome`; successful commands could remain UNKNOWN. Also, treating an integer result greater than zero as success incorrectly classifies successful zero-valued commands.

Fix: use Brigadier result callbacks, add the explicit outcome, correlate requested operation/command IDs, and report `command_execution` rather than inheriting a behavior-test assertion domain. Missing callbacks or contradictory receipts remain UNKNOWN. No automatic mutation retry was introduced. Tests demonstrated the failure before the fix, and the real live run subsequently verified zero-result success and exactly-once mutation.

### 2. Wrong assumptions about Forge's world defaults

[Run 36380185400](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36380185400) at `400838443cd35a491acf8a9395f96a550cce608a` built and started the real server, but the observer correctly refused a world-seed mismatch. The fixture assumed seed0 and a gametestserver directory without creating server.properties. Forge GameTestMain invokes the normal server Main path, which uses DedicatedServerSettings.

Fix commit: `b06dec4d052de1ff5680d4d6d5fb563de541f92f`. The fixture now creates seed/name/network settings exclusively inside the fresh run directory. The identity guard was not weakened. Forge1.20.1's `PrefixGameTestTemplate(false)` also removes the class prefix from test IDs; expected IDs were corrected to the actual `bridge` and `knownbad`.

Primary source locators: MinecraftForge/MinecraftForge `1.20.1`, `GameTestMain.java` blob `0312672d8dfdbb4d99073b3ac1105b8e051d74e2`; `patches/minecraft/net/minecraft/server/Main.java.patch` blob `aa6e1e551dc1b1b0c59115d26d5a30f3a917880b`; `GameTestRegistry.java.patch` blob `c665054b71ebccf02d51cf238aa59d2e432af565`. The branch label is context; those blob identities and observed run are the exact evidence.

The original server.properties bytes are retained as input evidence. Main normalizes that file at startup, so this fixture does not falsely register it as runtime-immutable. Its explicit runtime_config_files list is empty; the run is not proof of every dynamic Forge configuration value.

### 3. Counting an incomplete ambient-entity sample

[Run 36380851488](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36380851488) at `b06dec4d052de1ff5680d4d6d5fb563de541f92f` reached authenticated observation and executed the registered commands. It then failed because the fixture counted ambient pigs in a 128-entity truncated page: that page contained 30 pigs and was not a complete world inventory.

Fix commit: `3fa14453327e7992231e3d479ac1d1eebbd96b3c`. Give the fixture entity a known UUID and use the existing exact UUID/dimension query. Do not raise/remove resource limits, assume the first matching species is the target, or infer absence from a capped list. The independent scoreboard assertion still proves exactly-once mutation rather than relying solely on UUID uniqueness to suppress duplicate spawns.

These are real development/integration findings, not new claims about upstream Twilight Forest or Connector defects. They are recorded here as a scoped repair account; no claim is made that this document automatically created canonical FailureCase knowledge in the Core.

## Review and boundaries

Author self-review, **not an independent subagent audit**. Checks retained exact source/build/run/world correlation, bounded loopback input/output, separation of observation from mutation, explicit registries, no blind write retries, per-test negative controls, and separate assertion domains. Local tests ran before publication, followed by the complete hosted suite and the real game run. The local supplied-file checkout was partial; it was not represented as a full-repository local verification.

Still unproven: client rendering/screenshots/network correctness, Windows execution behavior, production MOD performance/correctness, actual Vineflower/tiny-remapper providers, the new Core bridge with real research records, a full real-MOD editing acceptance cycle (U01-U06/A01-A24), and per-target upstream failure-history investigations. Existing Twilight-first/Connector-next ordering remains unchanged.

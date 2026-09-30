# Bounded runtime batch — 2026-09-30

**The current plan remains incomplete. No new staff-client or Hydra visual
acceptance passed in this batch. Deferred usability improvements remain deferred.**

The [derived result record](verification/runtime-live-batch-2026-09-30.json)
contains versions, run/receipt identifiers, hashes and process outcomes. Original
private logs, sessions, paths, world files and receipts are retained separately;
this summary is not a hash-identical copy or public evidence closure.

## Verified implementation checkpoint

Commit `87d2086b4121167e5c3baa19da8963692b8e0450` contains the dedicated observer,
scoped dependency identities, fixed staff evidence readers and integrated Hydra
selection/probe. All 52 published blobs matched tested bytes. The local aggregate
passed 1,739 tests, with 103 PostgreSQL-dependent skips and one known ambient-parent
Git directory fixture excluded. Actual Forge 47.4.6 / Minecraft 1.20.1 / Java 17
observer compilation passed.

The automatic [push run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36723285026)
and [PR run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36723294549)
each passed 1,585 tests with 259 skips and eight warnings. The PR tested synthetic
merge `d82261ba5e9fad55deb23af54cceffe7e907f153`, containing the exact source head.
Optional cached adapter/Java checks also ran locally; the hosted skip XML was not
retrieved. The unchanged Blockbench workflow correctly did not match these paths.

## Actual run outcomes

The one approved cloud window began at 13:43:24 UTC with an absolute 14:08:24 UTC
cutoff. The disposable loopback server's EULA file was explicitly accepted under
the disclosed [Minecraft EULA](https://www.minecraft.net/en-us/eula).

- **Staff server:** the fresh world started and the authenticated observer answered.
  The limited-permission registered `stop` command did not complete. The exact
  session-bound JVM was then stopped with SIGTERM; its parent execution's nonzero
  result remains FAIL. This is not a server gameplay-test PASS.
- **Staff receivers:** both clients stopped during profile preflight, before a
  session, accepted launch operation, JVM or native gesture. Revalidation found
  an empty optional generated-resource directory where the original capture had
  recorded absence. The read-only target/dependency guards stayed enforced.
  Additional recovery was not executed after the original retry bound was
  exhausted; proposed removal of empty prepared directories was not performed.
- **Hydra attempt 1:** the JVM exited 1 before a client window because effective
  launch arguments contained two `gameDir` options.
- **Hydra attempt 2:** a fresh world/epoch used the ordinary Gradle-provider repair,
  but the JVM again exited 1 before a window. The fixture check had not covered
  ForgeGradle's later RunConfig argument append. No rendering result is inferred.

The retry controller closed at 14:06:30 UTC. All original execution threads were
closed by 14:07:59 UTC. The independent desktop process scan at 14:08:33 UTC found
zero owned game or test/native helper processes. No further launch followed the
window.

## Repairs and remaining gate

A focused repair now treats only a proven directly empty optional resource
directory as the same absent-byte scope. Nonempty, nested, symlink, unreadable,
unstable and missing mandatory roots remain rejected. Independent verification
passed 82 focused tests. This does not weaken the complete dependency inventory
or promote the original broad UNKNOWN profile.

Cached ForgeGradle 6.0.54 bytecode confirms that `MinecraftRunTask.exec` appends
RunConfig arguments after `doFirst`, separately from ordinary JavaExec argument
providers. The final repair validates arguments at Gradle's last argument-provider boundary,
after inherited Forge setup. It leaves Forge's token map/action intact and accepts
relative `gameDir=.` only when it resolves to the exact owned working directory.
Original providers see stock JVM/environment/property setup; their results are
captured once. Escapes, duplicates, missing values and option terminators reject
before process creation. A shared stateful lazy token remains one evaluation.

The actual cached `MinecraftRunTask` action and `JavaExec.copyTo` passed **35
independently rerun cases**, with only final process creation replaced by a
capturing action. This is stronger than the earlier ordinary-provider fixture,
but still not a Minecraft launch. Final init-script SHA256:
`5b2b4f5244678280bc28246897e49c1ec5967dcc5be7050bd97b351ba04e5193`.
Both earlier live failures remain FAIL; live verification of this final repair is
still NOT_RUN.

The subsequent aggregate recorded 1,783 passes, 103 PostgreSQL-dependent skips,
one unchanged sandbox-only deselection and 10 test-fixture compilation failures.
Those ten cases had been collected before a variable-name correction in their
Groovy harness; all ten corrected cases then passed in a separate run. The
production repair bytes were unchanged. These are two retained results, not a
claim that the failed aggregate was a clean pass. New-head hosted CI is reported
separately on the PR.

The [separate failure and repair history](history/2026-09-30-runtime/FAILURE-REPAIR-HISTORY.md)
retains both contrary live results and the two insufficient intermediate fixes.
Its exact captured import and verification records are historical snapshots;
`publication: NOT_PERFORMED` describes their capture time. Existing M2 history
remains unchanged. These derived public summaries reference original evidence
hashes; they do not expose the raw private evidence or establish runtime acceptance.

Dedicated propagation, non-invoking-player/client mutation checks, new clear item
views and U04 Hydra visibility remain NOT_RUN. Existing earlier GameTest,
Blockbench and bounded client results retain their original scope. Windows native
input remains unsupported; performance and whole loaded-class completeness remain
unestablished. No canonical promotion or deployment occurred.

A fresh live budget requires a separate bounded recovery decision. This record
neither authorizes another launch nor marks the current plan complete.

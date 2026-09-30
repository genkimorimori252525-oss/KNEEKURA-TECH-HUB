# Minecraft AI Usability Layer: scoped acceptance

Status: **COMPLETE_SCOPED_AI_USABILITY — SOURCE GATE AND ACTUAL TRIAL PASSED.**
Recorded: 2026-09-30 22:08:28 UTC
Source commit: `9941c9f7e6909bf11cd05d4237d9fe4cbfac1f7b`
Source tree: `0693882dd8663937f27a26da4791debdc7d8b832`

The [minimized machine-readable record](verification/AI-USABILITY-ACCEPTANCE.json)
is the detailed measurement/evidence reference. This accepts the thin task facade
and the bounded secondary state/next-action and lineage concerns for one actual
local coding harness. It does not promise general artifact delivery or establish
a universal usability score. The [original scoped MOD-AI acceptance](CURRENT-ACCEPTANCE-2026-09-30.md)
remains separate and unchanged.

**Publication gate:** the source-gate runs below attest the source commit above.
Use the [current PR](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/74) checks for the exact published documentation/report head.
This record cannot attest its own future commit ID; source CI is not evidence
that a later report commit passed. Implementation and scoped trial acceptance
are closed independently of that publication verification.

## Trial task and boundary

Two independent coding agents used one disposable copy of the existing pure staff
use policy from `tools/ci/mod_ai_staff/java/org/kneekura/staff/StaffUsePolicy.java`.
The declared source target was Minecraft **1.20.1 / Forge 47.4.0 / Java 17**; it
was not a resolved Forge build. The delivered repository staff source was unchanged.

The first agent was asked to add `decide(clientSide, coolingDown, abilityEnabled)`
and `DISABLED`, while preserving the original two-argument overload as enabled.
Client-side cases must always acknowledge; disabled server-side cases take
precedence over cooldown. The 60-tick glow and 100-tick cooldown constants were
unchanged. No network, external communication, Gradle, Minecraft, Blockbench or
native input was part of the exercise.

The agent began with TaskRequest and explicit existing references, used
`task prepare`, then expanded evidence through the existing CLI. It was not given
a hand-written internal-adapter map. The expected pre-edit RED was six Java
compiler errors for the missing overload/enum value, exit 1. One edit then passed
**14 Java policy assertions**, exit 0. This is pure-policy acceptance, not Forge
integration, distribution installation, gameplay, rendering or performance proof.

## Measured first-edit path

| Measurement | Observed result |
|---|---|
| Manually discovered commands | 3: `search`, `context`, `inspect` |
| Help calls before the first correct edit | 4 |
| CLI calls before the first correct edit | 8 |
| Edit attempts | 1, verified as the first correct edit |
| Retrieved task-data bytes before that edit | 18,078 |
| Canonical TaskContext bytes | 3,150 |
| `task prepare` CLI stdout bytes | 3,755 |
| Invalid/unsafe operations observed | 0 |
| Off-recorder task reads reported | 0 |
| Post-edit test | 14 policy assertions passed; no Minecraft execution |

The byte count covers recorded task-data output: task-file reads, CLI stdout/stderr
and expected pre-edit compiler diagnostics. It excludes unmeasured setup/context
input, tool protocol and editing overhead. **Tokens were not measured.** These
bytes are not full model-context use,
and there is no controlled before/after comparison.

Observed friction: the first agent consulted four help outputs and made an extra
`context` expansion between `search` and `inspect`. CLI/JSON still completed the
task without assistance; no unresolved transport limitation was observed.

## Fresh-agent resume

A fresh agent received the retained TaskRequest, canonical TaskContext and first
agent's handoff. It repeated **no initial CLI discovery or search**, made **0 CLI
calls**, performed **1 direct read of the identified source**, and made **0 source
edits**. Its recorded reads and test output totalled **8,531 bytes**. It again
passed the same **14 Java policy assertions**, exit 0; these overlapping assertions
are not 28 independent tests. No invalid/unsafe operation was observed and no
off-recorder task read was reported.

The retained index is the **immutable pre-edit source snapshot**. TaskContext alone
does not contain the edit outcome: the handoff supplied it, and the fresh agent
verified the identified edited source. Resume success must not be described as
an automatically refreshed index or a self-updating task state store.

## Evidence and independent checks

- TaskRequest hash: `4918617a6c59402d807089475d5d1b0c99a218c055d4066de78bf7f0e605f99c`
- Profile: `d1c72448134c8479ef09776d5fa1c7758be338fc03d3dd5a31b201640eb01955`
- Index: `4aa48f54e122f4f12621035f6efa86fe0f89f7440022824aa400cdb1e7a0b195`
- Document: `8dcd95be5bab06bd1a4b22644402b57006eb7b3693af3d66ecab477b0da16d9d`
- Canonical TaskContext SHA-256: `302a0640b1d76b6ad13fb1463258646966a11433458f9535205a317677ed59d2`
- Handoff SHA-256: `94735e3a945e4e53e0da75af2bd72347e44a3994fecde4d7a20c6b8695a50686`

Independent checks verified **24 recorded stdout/stderr pairs (48 hash checks)**, the unchanged
checker/recorder and unchanged delivered staff source. The JSON retains the source
before/after, checker and measurement-log hashes. Raw private paths, sessions,
receipts and logs are not published. A content hash is an evidence reference, not
permission to share its underlying contents.

No new facade defect or unsafe operation arose in this actual trial. The expected
missing-feature RED remains trial evidence; it is not relabeled as a gameplay or
system failure, and no artificial Failure / Repair History entry was created.

## Code gate and exact scope

Final-source local focused/packaging checks passed **1,072 tests, 0 failed, 0 skipped**
on the source tree above. Python was **3.12.14**, Java **Temurin 17.0.20.1+1**.

Both the [source push run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36782327788)
and [source PR run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36782332457)
succeeded: each recorded **2,695 passed, 331 cached-dependency skips, 0 failed,
0 errors and 8 warnings** out of 3,026 cases. Both runs' footer counts were
independently confirmed. Counts from the two runs are not
added. The push artifact's commit record is the exact source commit above;
artifact SHA-256 is `0cf259773d555e762adb097627c9b8528b065585b98a0234e56dc5a54f61f4e1`.
The hosted Python/Java versions match those stated above.

The **verified push artifact** supplies the following detailed breakdown of its
331 skips. This category breakdown is distinct from the independently confirmed
footer counts for both runs:

| Count | Reason |
|---:|---|
| 194 | Explicit cached GSON_JAR required |
| 1 | Explicit cached MINECRAFT_FORGE_JAR required for patched lifecycle ordering |
| 24 | Explicit cached GROOVY_JAR and installed Java required; no downloads |
| 10 | Explicit cached Groovy/Gradle and Java required; no downloads |
| 35 | Explicit cached Gradle8.8/ForgeGradle6.0.54/srgutils and JDK required; no downloads |
| 19 | Explicit already acquired GSON_JAR required; Java compile remains a separate gate |
| 6 | Explicit cached Gson and Netty common/buffer/transport classpath required |
| 40 | Explicit cached Gson required |
| 1 | Explicit cached Forge classpath and Java17 JDK required |
| 1 | Cached Forge 1.20.1-47.4.6 resolved export required; no download or launch fallback |

The earlier local aggregate at `86382cce1b285493e6ff03ccaddc589db763fac6`, before the
final identity fix, remains **2,850 passed, 104 skipped, 1 failed**. Its failure was
`test_private_parent_validation_allows_real_external_directory`, caused by an
injected Git ancestor in permitted temporary roots; it was not excluded or
rewritten as PASS. Its skips were 103 unset PostgreSQL test configurations and
1 missing explicit cached Minecraft Forge JAR. That older aggregate does not
attest the final source fix. Hosted results and local focused coverage retain
their different prerequisites rather than treating skips as passes.

## Decision and stop point

**MCP: NOT_NEEDED for this actual local coding harness.** CLI/JSON plus the retained
handoff completed the task and fresh-agent resumption. No MCP implementation is
added; a different harness would need concrete transport friction and a separately
bounded decision before changing that choice.

The planned thin facade, scoped trial and secondary state/next-action and lineage
acceptance are complete. Stop this implementation here, and use the [current PR](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/74) checks for separate
exact-head publication verification. Asset-editing Candidates 1–3 and the
KNEEKURA-LAB experimental runtime bridge remain deferred/unimplemented.
Windows/native-input scope, unmeasured performance, human canonical promotion,
Connector beta.50 compatibility UNKNOWN and all other original scoped limits
remain unchanged. One source-policy exercise does not extend those claims.

# Twilight Forest Runtime R1 Verification

Status: **verified**
Scenario: **R1 — dedicated-server startup**
Successful run: `35795408650`, attempt 2
Runner: `Jolly-TechHub` (Windows / X64)

## Verified inputs

- ANCHOR source: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- FRONTIER source: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- runtime probe SHA-256: `31226eaa0f38485f5efc282c956cbe77c6c7a6efbe25142854bfec5931a741c8`
- successful attempt TECH HUB input: `6dfe3a10cc5278ea060ef34432604d63ce176d57`
- compact evidence commit after the successful attempt: `fa130ce4e791deddb83533a281740908907e9a2a`
- raw logs: GitHub Actions artifact `10727157457`

The successful attempt reused the same R1 workflow/probe logic after previous attempts had populated persistent Gradle/tool caches on the self-hosted runner.

## Verified R1 observations

| Track | Minecraft / loader | Dedicated-server ready | Load marker | Mod construction marker |
| --- | --- | ---: | ---: | ---: |
| ANCHOR | Minecraft 1.20.1 / Forge 47.1.70 | 474.393019 s | 450.978543 s | not separately observed |
| FRONTIER | Minecraft 26.1.2 / NeoForge 26.1.2.102 | 729.706270 s | 725.806108 s | 718.505653 s |

Both tracks reached the dedicated-server ready marker with `timed_out=false` and `stop_command_sent=true`.

The probe later used forced process-tree termination because the Gradle wrapper process did not exit within the probe's shutdown window after the Minecraft stop command. That shutdown behavior is **not** treated as a startup failure and is **not** a graceful-shutdown measurement.

## Interpretation boundary

This successful R1 record proves that both pinned development trees can reach dedicated-server ready under the recorded environment.

It is **not** a cold-start benchmark and must not be used to claim that ANCHOR is generally faster than FRONTIER, or vice versa. The successful attempt ran after earlier attempts had warmed persistent Gradle/tool/asset caches, and the tracks use different Minecraft, loader and Java generations.

R1 does not measure:

- first Twilight Forest dimension entry
- chunk-generation distributions
- structure-generation cost
- boss tick cost
- multipart stress
- client rendering
- network throughput
- resource reload
- an overall performance score

## R2 boundary

The next runtime scenario is **R2 — first Twilight dimension entry**.

R2 must be a separate scenario with a fixed world seed and fixed portal/entry location. It should capture portal transition latency, first required chunk generation, server tick spikes, allocations and generated-structure activity. R1 timings must not be relabeled or reused as R2 evidence.

Raw logs remain artifact-only; compact derived evidence and hashes remain in TECH HUB.
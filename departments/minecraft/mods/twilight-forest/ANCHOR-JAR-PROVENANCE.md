# Twilight Forest 4.3.2508 — Distributed JAR Provenance

Status: **distributed binary pinned; resource correspondence strongly proven; compiled-class identity kept as a separate proof boundary**

## Distributed artifact

- CurseForge project ID: `227639`
- file ID: `5468648`
- release: `4.3.2508`
- filename: `twilightforest-1.20.1-4.3.2508-universal.jar`
- exact size: **23,332,091 bytes**
- SHA-256: `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`
- SHA-1: `fa3b506a45d3e9c465551cd533fd50c899496e9f`
- ZIP entries: **7,752**
- class entries: **1,570**
- non-class/resource entries: **6,182**

The manifest inside the actual distributed JAR records:

- implementation version: `4.3.2508`
- implementation timestamp: `2024-06-24T18:00:24+0000`
- specification vendor: `TeamTwilight`

`META-INF/mods.toml` records Forge loader `[47,)`, Forge dependency `[47.1.0,)`, and Minecraft dependency `[1.20.1,)`.

## Public-source candidate

Pinned source commit:

`TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`

The candidate commit timestamp is 2024-06-24 17:58:45 UTC, immediately before the JAR manifest build timestamp, and its Discord URL change matches a 4.3.2508 release-note change.

## Executed resource correspondence proof

The verifier ran on the KNEEKURA-LAB Windows/X64 self-hosted runner in workflow run `35742278246`.

It compared every eligible `src/main/resources/` and `src/generated/resources/` source resource against JAR bytes using Git's exact blob identity:

```text
SHA1("blob " + byte_length + NUL + raw_bytes)
```

Result:

- expected source resource paths: **6,156**
- paths present in both source and JAR: **6,156**
- exact Git-blob matches: **6,156**
- mismatches: **0**
- source paths missing from JAR: **0**
- match ratio: **1.000000**

Machine-readable record: `ANCHOR-JAR-EVIDENCE.json`.

Conclusion: **RESOURCE_CORRESPONDENCE_STRONG**.

## Proof boundary

This result proves the distributed artifact identity and exact correspondence of the compared resources to commit `a7dd8f13…`.

It does **not** by itself prove that every compiled class was produced from that exact source commit, because the Java build path includes compilation, mappings/remapping and reobfuscation. A reproducible build / class-semantic comparison would be a separate experiment if that stronger claim is ever needed.

Therefore the Hub records both facts without conflating them:

```text
distributed JAR identity       = pinned
resource correspondence       = 100% exact for 6,156 paths
metadata/chronology           = strongly consistent
compiled-class identity       = not independently proven
```

## Later source divergence warning

Upstream issue #2345 later records a developer statement that a Japanese translation fix existed in source but apparently was not uploaded to CurseForge. Later 1.20.1 branch state must therefore not be substituted for the pinned distributed artifact.

The ANCHOR track uses the exact JAR hash plus the pinned `a7dd8f13…` source snapshot and keeps later source changes as separate evidence.

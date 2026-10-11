# Warfare Wings — owner runner readiness and exact-artifact gate (2026-10-11)

Current observed runner: `Jolly-TechHub`, labels
`self-hosted, Windows, X64, tech-hub, kneekura`. At the
2026-10-11 validation it was **online and idle**, and successfully accepted
owner Windows workflow [#38109783517](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38109783517).

Actual GitHub Actions evidence:

1. Checkout, Temurin Java 17, and Gradle setup: **PASS**.
2. `Stage exact runtime jars`: **FAILED** with
   `Exact user-owned Warfare Wings ANCHOR not found`.
3. All real Minecraft GameTests, including 5 single-plane tactical tests,
   3 new live squadron tests and A6M calibration: **NOT_RUN**.

The original researched Warfare Wings SHA-256 is
`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`.
A byte-for-byte check of a publicly hosted Warfare Wings 1.1.4 Forge JAR
(29,568,717 bytes) gave SHA-256
`3b6b245e703862517fe7aae6acd95ccafc865e1e81ba7a26e2b9abcfe1120187`,
which **does not match** the previously supplied research artifact. The
comparison download was removed from the ignored local cache. Do not use
this public JAR as evidence of the user's same-artifact physics.

The pinned Immersive Aircraft 1.3.3 runtime SHA-512 is
`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`.
The owner workflow automatically downloads that particular pinned Modrinth
version **only after** locating the exact user-supplied Warfare Wings JAR,
and then independently hashes it.

## Next executable runtime step

Store the user's **original** Warfare Wings ANCHOR JAR on the Windows
Jolly-TechHub runner at a path readable by its account. Do not commit or
upload the JAR to this Git repository. Verify it with:

```powershell
$wwAnchor = 'C:\ABSOLUTE\PATH\TO\warfare_wings-1.1.4-1.20.1-forge.jar'
(Get-FileHash -LiteralPath $wwAnchor -Algorithm SHA256).Hash.ToLowerInvariant()
```

The digest must equal the exact SHA-256 shown above. Set the optional
`warfare_wings_path` input to this absolute path when dispatching
`warfare-wings-physics-ai-runtime.yml` for branch
`jolly/research-warfare-wings-2026-10-07`, or configure the runner process
environment variable `KNEEKURA_WW_ANCHOR_JAR`. The workflow also checks
the runner account's top-level `Downloads` and `Documents` folders for
the exact canonical filename.

Only after that gate is **PASS** may GameTest spawn the actual registered
aircraft. Source-only ForgeGradle compilation, Docker tests and synthetic
telemetry are not substitutes for this step. Failure is intentional and
preserves provenance.

## Evidence to accept afterward

The workflow must pass old A6M header + 401 records, five independent
single-aircraft control CSVs (header + 181 records), live team-pair and
same-team CSVs, server-side FOV/occlusion GameTests, and strict
`verify_tactical_runtime_receipts.py` checks. Review elapsed tick order,
real yaw and displacement, IA X/Z smoothing, terrain hazard decisions,
equipment API availability and physical parity separately. The comparator
currently operates as a **calibration investigation with no acceptance
tolerance**; GameTest success alone cannot promote all 24 aircraft's
source-model performance rankings to real Minecraft parity.

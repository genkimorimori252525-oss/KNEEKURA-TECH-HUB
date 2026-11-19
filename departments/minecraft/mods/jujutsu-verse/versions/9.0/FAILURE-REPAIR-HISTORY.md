# Jujutsu Verse 9.0 — failure / repair history

**Track:** ANCHOR (Minecraft 1.20.1 Forge, user-supplied 9.0 JAR, SHA-256 `fdf1f8a6c28833c093dc778764b5a6147fc0552ec34e172f918fa4be8dccc065`)

**Status:** `NOT_ANALYZED`. This report does **not** claim a reviewed set of author Issues, PRs or before/after repair commits.

## Bounded discovery leads

- Official 9.0 changelog: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/9609792 (lists VFX/compatibility changes as **AUTHOR_CLAIM**).
- Prior 8.1 research: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/100 . The binary was separately pinned, but neither code-level history nor a reproduced repair was verified here.
- Candidate symptom families: external shader pack visibility, terrain rollback after chunk unload, multiplayer domain clashes, server-side beam hit scan performance.

## What would be needed

1. Establish author-controlled public issue/source locations, if available, and capture a bounded issue/PR search inventory.
2. For each supported repair claim obtain actual before/after revisions or public release artifact deltas and versioned reproduction conditions.
3. Keep issue claims, static bytecode and runtime observations independent.
4. Store captured source or restricted binaries outside Git; publish only permission-appropriate hashes and locators.

Until these steps are performed, cases remain empty. See [machine-readable status](FAILURE-REPAIR-HISTORY.json).

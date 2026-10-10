# Fungal Infection: Spore — Minecraft AI technology analysis

**Target:** Fungal Infection: Spore 2.2.0j / Minecraft 1.20.1 Forge, Harbinger  
**Research snapshot:** 2026-10-11  
**Status:** IN_PROGRESS — important Proto/Womb/Mound/Group/Volley bytecode methods MAPPED; 1,350 classes total, selected 183 classes dumped; runtime NOT_RUN; not whole-target COMPLETE.

## Read here

- [Hivemind / group AI / ecology / volley technical findings](HIVEMIND-AI-BYTECODE-2026-10-11.md) — exact selected original class-method evidence, 4×4 policy, weight updates, feedback call path, target sharing, resource circulation, performance hypotheses, negative claims.
- [JAR evidence and verification limits](ARTIFACT-RECEIPT-2026-10-11.json) — exact uploaded artifact byte size and SHA-256, mods.toml metadata, source/release/version boundaries.
- [AI department — hierarchical command plan](../../../ai/multi-agent/HIERARCHICAL-COMMAND-AI-v0.md) — independent KNEEKURA design proposal, not proven to exist in original Spore.
- [Original MOD shortlist](../../../ai/multi-agent/MINECRAFT-MOD-SCOUT-2026-10-11.md) — historical reconnaissance performed before JAR acquisition.

## Key findings

1. The original Proto Hivemind really uses a 4-input / 4-output linear scoring system. It updates the selected action row by +0.05 on attributed positive damage feedback and -0.10 on attributed negative damage feedback, with bounds [-1,1]. It persists its own weights to NBT. **Not proof of deep neural learning or a global learned model shared among all hiveminds.**
2. The surrounding organisms split work: Proto for conditional summon/target selection, Womb for gathering and assimilating infected Mob resources, Mound for expanding infestation, HiveTumor for producing Proto, and upper-order AIs for propagating targets/search positions.
3. ScatterShotRangedGoal implements a variable number of same-update ranged calls. Projectile spreading angles and specific resulting in-game bullet patterns are yet to be verified.
4. Experimental ExpPathFinder delegates to the vanilla PathFinder and wraps Path. Its path name does not by itself establish neural-pathfinding machinery.

## Provenance

Original JAR: spore_1.20.1_2.2.0j.jar, SHA-256 **d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489**, size **116,439,461 bytes**. Author/loader and license from mods.toml (All Rights Reserved). Binary equivalence to downloaded official release is not established; raw JAR/decompiled source/assets/sounds are deliberately not committed to public TECH-HUB.

- ANCHOR: MC 1.20.1 Forge, original uploaded JAR.
- FRONTIER: public MC 1.21.1 NeoForge release is separately known; binary NOT_ACQUIRED/NOT_REVIEWED.
- EVIDENCE: targeted static reads; game execution, multiplayer, TPS, visual performance and server correctness are **NOT_RUN**.

All further MOD research follows [Minecraft analysis workflow](../../ANALYSIS-WORKFLOW.md) and [specification](../../ANALYSIS-SPEC-v1.md) and keeps previous historical findings intact.

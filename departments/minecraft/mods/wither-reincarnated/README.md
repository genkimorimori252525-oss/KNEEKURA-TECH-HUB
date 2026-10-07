# Wither: Reincarnated — ANCHOR static analysis

Status: **STATIC ANALYSIS COMPLETE / RUNTIME NOT RUN**  
Track: **ANCHOR — Minecraft 1.20.1 + Forge**  
Target: **Wither: Reincarnated 1.0.5**  
Analysis date: **2026-10-08**

This directory records a bounded technical analysis of the user-supplied
`witherreincarnated-1.20.1-1.0.5.jar`.

The purpose is not to redistribute or clone the MOD. The JAR declares
**All Rights Reserved**. Raw JAR bytes, decompiled source trees, textures,
models and sounds are therefore not stored here.

The retained material is limited to:

- exact artifact identity and provenance;
- class/package/Mixin/tag/network maps;
- derived behavior contracts from bytecode/resources;
- implementation lessons that can be reimplemented independently;
- explicit boundaries between static evidence and runtime claims.

## Exact artifact

- file: `witherreincarnated-1.20.1-1.0.5.jar`
- size: `12,807,443` bytes
- SHA-256: `00589726de7d82628d92761394a8a3e6b153c28942f50c9ae6ba7860b0fab80a`
- mod id: `witherreincarnated`
- version: `1.0.5`
- loader: JavaFML / Forge `[47,)`
- Minecraft: `[1.20.1,1.21)`
- author metadata: `Alexander's Fun and Games`
- declared license: `All Rights Reserved`
- classes in JAR: `102`

See [ANALYSIS-RECEIPT-2026-10-08.json](ANALYSIS-RECEIPT-2026-10-08.json).

## Main technical result

The MOD keeps vanilla `WitherBoss` as the gameplay entity but substantially
rewrites its behavior through Mixins, then installs a modular attack stack:

1. `WitherBarrageGoal`
2. `WitherLaserGoal`
3. `WitherChargeGoal`
4. `WitherBackUpGoal`
5. `WitherRangedAttackGoal`
6. `WitherRandomTravelGoal`

Flight is also replaced by `WitherMoveControl` and `WitherNavigation`.

The result is not a Bedrock Wither implementation. It is an independent boss
redesign and must not be used as evidence for Bedrock gameplay constants.

## Documents

- [CODE-MAP.md](CODE-MAP.md) — package, Mixin, goal, tag and packet map
- [AI-BEHAVIOR.md](AI-BEHAVIOR.md) — phase bands, attacks, projectiles, possession and world interaction
- [NETWORKING-RENDERING-PERFORMANCE.md](NETWORKING-RENDERING-PERFORMANCE.md) — synchronization, client state, FX and cost surfaces
- [LICENSE-PROVENANCE.md](LICENSE-PROVENANCE.md) — rights and reuse boundary
- [TECHNIQUE-HARVEST.md](TECHNIQUE-HARVEST.md) — selected reusable engineering lessons
- [../../techniques/wither-reincarnated-boss-engineering.md](../../techniques/wither-reincarnated-boss-engineering.md) — cross-target technique note

## Evidence boundary

What was done:

- JAR inventory;
- metadata/resource inspection;
- Mixin/tag/access surface inspection;
- JVM class and bytecode inspection;
- selected configuration/default-value recovery;
- cross-check against the existing KNEEKURA Bedrock Wither reconstruction.

What was **not** done in this pass:

- launching Minecraft with the MOD;
- gameplay timing capture;
- TPS/profiler measurement;
- multiplayer/network traffic capture;
- visual parity or shader testing;
- source-to-binary equivalence, because no authoritative public source tree was established.

Any runtime/performance statement in these notes is therefore a **cost hypothesis
or static upper-bound observation**, not measured performance.

## Bedrock Wither boundary

For the KNEEKURA Bedrock Wither reconstruction, this target is classified as:

**REFERENCE — Java boss engineering only.**

Useful ideas may inform independent implementation, but:

- Reincarnated health thresholds are not Bedrock evidence;
- Reincarnated cooldowns/damage values are not Bedrock evidence;
- its `WitherBoss` Mixin architecture is not adopted as the behavioral base;
- its assets/code are not copied;
- Bedrock behavior remains governed by Mojang/Microsoft definitions, current BDS
  structure, direct observation and Bedrock-specific technical evidence.

# Bedrock Wither — Timeline

## 2026-10-02

- Bedrock Wither reconnaissance began from official Bedrock Creator material, technical/community behavior documentation and community reports.
- Reconstruction strategy changed from "modify Java Wither" to an independent `Monster`-based boss so Java-specific AI cannot silently leak into the target behavior.
- BEStyleWither was found and pinned as comparative prior art for both a 1.20/1.20.1-era track and the later 1.21.1 track.
- Evidence, design and acceptance were placed under the Minecraft Technology Department.
- A root-level `deliverables/` boundary was introduced so KNEEKURA TECH HUB remains a technology/research repository rather than becoming a Wither MOD repository.
- Bedrock Wither became the first Minecraft deliverable using the permanent product/history/adoption/evidence layout.

## 2026-10-03

- Resumed from the complete local-AI handoff and current STATUS/ADOPTION, on an isolated branch based on `c1221d3`.
- Reproduced two implementation defects with real Forge GameTests: healthy reload disabled later death completion; spawn visuals consumed an unsynchronized local timer. RED: 19/21 passed; only the intended new regressions failed.
- Applied minimal lifecycle/synchronization repairs without changing Bedrock constants. Local build and all 21 required GameTests passed; independent source/actual entity-data bytecode review found no blocking issue. See BWR-0008, BWR-0009 and the compact 2026-10-03 receipt.
- Prepared direct Bedrock measurement scenarios v1 for the existing Phase 0/4 plan. No direct Bedrock run, real-client/Tank acceptance, merge or deployment was performed.

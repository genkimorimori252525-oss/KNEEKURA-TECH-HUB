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
- Published the first packet as Draft PR #81 at `1d067f087222a1a7efffe55cb3fc459f1b581b30`; dedicated hosted build/GameTest passed 21/21 and hosted TECH HUB passed 3141 tests / 332 skipped / 8 warnings. The existing PR #75 branch stayed unchanged.
- Reproduced and repaired synchronous Forge death-cancellation/positive-health revival state corruption in aerial and active-dash fixtures. Local RED 21/23 → GREEN 23/23; BWR-0010 retains the exact scope and the rejected XP-absence hypothesis.
- Strengthened existing reward acceptance without changing product behavior: genuine survival-player kill credit, death/drop/XP hooks, actual 50 XP and one Nether Star, and repeated-lifecycle idempotency. Final local suite passed 24/24 twice on the same world; full TECH HUB remained 3038 passed / 435 skipped.
- Preserved BWR-0011 as a test-fixture failure/repair, not a product bug: an overbroad item precondition rejected unrelated terrain drops on reuse. Targeted preconditions and complete owned cleanup retain the original exact reward assertions.

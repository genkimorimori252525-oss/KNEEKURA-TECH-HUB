# Original Decision native hook evidence

## Exact generation and retained evidence

LAB commit `8c54e4f454f53f1507335c2caa8247b8873bdafb`, pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`, Minecraft 1.20.1 / Forge 47.2.0 / Java 17. The explicit development launch loaded `kneekura-decision.mixins.json`; required injections remained enabled. This is an applied native hook smoke, not resident post-Mixin byte attestation or full behavioral acceptance.

- Run `run-20261003082900-4e4563bfd3b8`, session `sess-20261003082900-a00b5cb1fae9`.
- Snapshot `snapshot-20261003082900-22ef2b20e302`, hash `55a4f38c956cdded4dabbee40efcddc09a916c0ab22a67a1aa3bc5f4085331aa`.
- 1,949 retained canonical rows; `EVIDENCE_COMPLETE`; final writer sequence 1,949, dropped 0, remaining queue 0, clean ACK.
- Original launcher/game exit verified by PID/start-time ownership checks. A later unrelated process reused the launcher PID; it was not stopped.
- Retained report SHA256 `4012e6a69bbc1d302caba7533b74243a3ad42b9362f96eb68118b3ea0c1e858c`.
- Raw SHA256 `33c9194bb50c3e36dc149f13435fb7c66a429d4095668c0af62d1f153f798645`.
- Original true tank save: all 85 source-manifest file SHA256 values unchanged after finalization.

Private artifacts are under `K:/kneekura-decision-native-data-20261003/native-r7`; no copied worlds, raw private logs, class bodies or JARs are committed.

## Actual coverage

| Selected case | Original events | Actual kinds | Terminal reason |
| --- | ---: | --- | --- |
| Zombie, burst OFF | 0 | none | not armed |
| Zombie, Goal | 256 | eligibility return 251; delegated start return 1; continuation return 4 | EVENT_BUDGET |
| Zombie, Path/Malus | 116 | base malus return 114; pre-cleanup search cache 1; actual Path return 1 | WINDOW_ENDED |
| Villager, Brain | 256 | Behavior tryStart return 188; tickOrStop return 29; Brain tick return 22; Behavior doStop return 17 | EVENT_BUDGET |
| Villager, Sensor | 76 | original Sensor doTick return 76 | WINDOW_ENDED |
| Ghast, controls | 256 | original virtual control tick return 256 | EVENT_BUDGET |
| Reimu, combined | 0 | none; original fixture has NoAI=1 | WINDOW_ENDED |

All 960 original events across 12 kinds passed the retained kind-specific decoder. The one Path search retained 15 cached nodes with open/closed/other roles; the other cached blocked node was not labelled an evaluated neighbor. The actual Path result reported `canReach: true`, 3 nodes, using the same search identity.

The native driver expected events from every armed case. Its Reimu expectation was wrong: read-only offline NBT inspection of the unchanged fixture proves entity `touhou_little_maid:reimu`, UUID `11111111-2222-2222-3333-333344444444`, `NoAI: 1`. The original failure/report is preserved, with a separate `noai-fixture-reconciliation.json`. Zero calls are not hidden or replaced by replayed AI. Operational maid deep-hook acceptance remains unverified. Goal stop instrumentation compiled and its producer contract passed, but no native `GOAL_STOP_RETURN` was observed in these finite windows.

## Retained read-only drill-down

The subsequent typed query CLI read the finalized canonical Path records at game tick 41001, selected revision 3 / Arena epoch 0. It returned 3 of the 15 cached nodes with explicit query truncation and the same actual Path result. Sources were `obs:forge-runtime:8780:553` and `obs:forge-runtime:8780:554`. Canonical and finalization hashes matched before/after the query. Missing results do not imply unreachable; cached nodes do not imply a complete evaluated-neighbor trace.

## Limits and next acceptance

Capture counters measure construction/encoding only, excluding final encoding, writer, consumer, Viewer and full server-tick cost. No negligible/zero observer-effect claim is made. The fixture did not force complete pursuit/ranged/aquatic/teleport behavior, install TF, or establish complete candidate populations or selection reasons. Live terrain queries, typed Mob SDK/TF proof, eight behavioral fixtures, synchronized projectile/hit links and controlled total observer-effect measurements remain pending.

At the frozen hook HEAD, both GitHub source runs and repository pytest succeeded in Draft PR #80. Local Windows LAB checks preserved four symlink `EPERM` failures and one inherited-pipe timing failure; assertions were not weakened. Portable Java and genuine mapped API checks passed.

# Native original MOD method-return acceptance

Frozen LAB `c2b1e8f459438752cd458211dff919b28e6e234a`; MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`; Minecraft 1.20.1 / Forge 47.2.0 / Java 17 / TF 4.3.2508. Source proof uses the mapped artifact and ten class resources from the [SDK ledger](TF-ANCHOR-MAPPED-BYTECODE-LEDGER-2026-10-03.json), matching the preceding native cached-state trial.

Fresh private trial native-r12 preserved the complete preceding native-r11 world. The copied eight-Vanilla fixture received four invulnerable/persistent TF entities, with Knight NoAI=false and the other three NoAI=true. A held-world-lock reread proved only those entity additions. The private existing experimental-confirmation flag has a level.dat backup and unchanged other NBT. Original user saves were not changed.

Run `run-20261003112306-871a6572a3ea`; snapshot `snapshot-20261003112306-40eae6b59486`; runtime PID 39420, process epoch 1, Arena epoch 0. Explicit debug hooks were enabled and reached DEBUG_READY.

| Selection | Revision | Original MOD returns | Terminal condition |
|---|---:|---:|---|
| Default OFF, Hydra | 1 | 0 | No burst requested |
| Hydra | 2 | 64 `advanceHeadState` | EVENT_BUDGET; 258,264 charged payload bytes, below 262,144 request |
| Knight Phantom, AI on | 3 | 2 `switchToFormation` | WINDOW_ENDED; 5,289 charged payload bytes |
| Snow Queen, NoAI | 4 | 0 | WINDOW_ENDED; NOT_CAPTURED |
| Ur-Ghast, NoAI | 5 | 0 | WINDOW_ENDED; NOT_CAPTURED |
| Reset OFF | 6 | 0 | No burst requested |

The two observed method kinds pass exact source/argument/post-state/owner/context validation. Hydra's method can return without changing state; the previous cached state is not an invocation-entry capture. Both stateChangeStatus and reasonStatus remain NOT_EXPOSED. Snow Queen/Ur-Ghast callbacks were not observed in this fixture, and their successful invocation capture is not claimed. No Vanilla callbacks leaked into the mod-only channel. This trial is not full Boss battle acceptance.

The original Hydra record at world gameTime 40,609 used local burst start counter 301; these clocks stay distinct. Finite summaries use the last-completed server END counter, while canonical records and typed timeline queries use actual world gameTime.

924 canonical records; writer dropped 0, remaining queue 0, clean shutdown ACK, verified process exit, EVIDENCE_COMPLETE. Original save: all 85 file SHA256 values still match.

Actual retained CLI `mod_returns` reads returned Hydra's seven head callbacks at the first captured tick (`obs:forge-runtime:39420:50` through `:56`) and Knight's callback `obs:forge-runtime:39420:334`. The normal packet limit of eight recent callbacks is explicit. Canonical/finalization hashes matched before and after these read-only queries:

- Observations: `d167bd4efa0934fc035128f5555d3e5e5e56c234a8a9650274f330ec142e1010`.
- Finalization: `0bf2345cd81612ac8516ef70ef3a9c45220ab8dfe5aa09524466e92f280fe7b9`.
- Private report: `c4c258dea4167422484a71f646bdb0593ecb819be014365032ba7e5ad134c2e6`.
- Raw evidence: `e9dd3125b42060ada9896d1768a4e299d598787e11c0bf2877a9e642941995c1`.

Captured payload construction/first-byte-check median: Hydra 58,700 ns, Knight 237,000 ns. This excludes final encoding, writer and Viewer; it is not controlled OFF/ON total observer-effect acceptance. Focused Node tests: 74 passed / 0 skipped; portable Java/descriptor interoperability, genuine Forge API and all bridge/Mixin compilation passed. Spatial/timeline presentation, full representative behavior scenarios and controlled observer cost remain separate work. Private JARs, worlds and logs are retained outside Git.

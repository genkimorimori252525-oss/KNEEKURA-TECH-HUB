# Native representative capture and observer measurements

These are bounded observations on fresh disposable copies of the user's actual debug-world fixture. They are not complete combat/Boss acceptance, complete AI inventory or proof of negligible observer effect. Minecraft 1.20.1 / Forge 47.2.0 / Java 17; unchanged MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`; exact TF original/mapped artifacts from the existing SDK ledger.

## Representative trial native-r13

Frozen LAB `85794a3ebb46e8730044e065e9d818816f5a0111`; run `run-20261003120721-a046e4f3a796`; snapshot `snapshot-20261003120721-4718d823bfcf`; runtime PID 43416, process epoch 1, Arena epoch 0. The previous private r12 world was preserved before copying the r3 baseline.

Prelaunch genuine NBT readback under the world lock confirmed: a private Survival player with 1024 health/regeneration, night/no spontaneous spawning/no mob griefing; eight persistent AI-enabled Vanilla fixtures; four AI-enabled TF fixtures; a bounded 66-block glass/water Dolphin pool. No observer replayed an AI method, phase setter or gameplay damage callback. The fixture changes only private level/player/entity/chunk files, with backups and reread verification. They change natural conditions and must be considered when interpreting behavior.

| Family / selection revision | Actual position samples | Original Vanilla callbacks | What is evidenced / limit |
|---|---:|---:|---|
| Zombie / 9 | 50 | 256 | Actual target, Goal start/stop and navigation returns; not every pursuit outcome |
| Skeleton / 10 | 52 | 256 | Target/control/eligibility/base malus; no ranged-hit acceptance |
| Villager / 11 | 28 | 256 | Brain tick/sensor/behavior returns; sampled motion with gaps |
| Ghast / 12 | 56 | 256 | Target and actual custom-flight motion; not complete projectile/hit chain |
| Phantom / 13 | 56 | 256 | Target/custom-flight movement; not every attack phase |
| Slime / 14 | 25 | 256 | Sampled jumps/movement and Goal/control returns; gaps remain gaps |
| Dolphin / 15 | 56 | 256 | Motion in the pool fixture; not all aquatic behaviors |
| Enderman / 16 | 48 | 256 | Goal/control/target observations; selected window positions around y=-60, not typed proof of how it reached them |

Every Vanilla burst reached its finite 256-event budget. Position counts are retained samples rather than forward-filled states. Stationary/unchanged keyframes can leave more than ten game ticks between samples, so a visual gap is not itself an AI failure or teleport proof.

Hydra revision 17 captured 121 original `advanceHeadState` returns; Knight revision 19 captured two `switchToFormation` returns. Snow Queen revision 18 and Ur-Ghast revision 20 had AI enabled and cached state/motion but zero original phase returns in their armed windows. The Snow selection lasted 45 seconds while its burst lasted only 200 ticks; zero does not establish that no phase changed outside that window. Phase-entry reason, full formation coordination and complete Boss battle remain unverified.

7,603 canonical records, dropped 0, remaining queue 0, clean ACK, verified exit, EVIDENCE_COMPLETE; original-save 85/85 SHA matched. Read-only actual Villager Decision CLI and the Motion consumer measurements preserved both canonical/finalization hashes:

- Canonical `eac7b48884035142148cfa98a3bf23ed0f883322bf91be7fc2676d19ad31cb0d`.
- Finalization `97e574d2757d73b15a0215f33ef2d86d2c6a104fb64b9f44335fb72ecb554521`.
- Private report `a6a4d69a11d290dda2b412a0f7f12fe662ebb0a63f3ca390047ea784fed735d0`.

## Same-JVM JFR request windows

JDK 17 JFR used the same CPU/thread CPU/file-write/execution-sampling settings for all eight windows. Each window lasted 20 seconds after a two-second settling interval; selected windows used the same Villager. OFF means no selected target, with debug runtime/Mixins still loaded. CPU numbers below are raw JFR mean JVM user+system fractions, not percentage-point observer increments.

| Sequence | Mode | CPU samples | Raw JVM fraction | Raw evidence writes / bytes |
|---:|---|---:|---:|---:|
| 0 | OFF | 19 | 0.09517 | 40 / 39,002 |
| 1 | Baseline | 20 | 0.04868 | 174 / 214,576 |
| 2 | Snapshot | 19 | 0.04325 | 222 / 651,742 |
| 3 | Burst | 19 | 0.04707 | 220 / 678,032 |
| 4 | Burst | 20 | 0.04252 | 243 / 723,525 |
| 5 | Snapshot | 19 | 0.04382 | 276 / 800,543 |
| 6 | Baseline | 19 | 0.04354 | 182 / 227,254 |
| 7 | OFF | 20 | 0.04062 | 40 / 39,242 |

Snapshot windows captured 88 snapshots each. Both burst windows reached EVENT_BUDGET 256 before the 20-second request interval ended: measurements include post-budget time. SERVER emitted observation clocks give about 19.999–20.003 ticks/second; heartbeat-only rows are insufficient when other lanes suppress heartbeat output. Source IDs and exact wall/game-clock endpoints remain in the private receipt.

Recording: 26,361,037 bytes; SHA `7eb165934012de96c4b4b4b1d58bef074bc6836f4f4ba055b43beaa8e2a3e59d`; 67,579 exported events. JFR repository/data were on K:. Receipt SHA `21fdba29043bd0279370eba8241d43d1f166fef129aaf93221ff03cbed03bf25`.

World AI, JIT/warmup and external scheduling evolve with time. Two reversed repeats are descriptive, not randomized paired-state experiments. JVM CPU includes server, client, async writer and other mods; GPU, OS-cache attribution and complete observer cost are not measured. Summed write durations can overlap and are not additive process latency. JFR itself has observer cost. No causal "negligible overhead" conclusion follows from these values.

Retained Motion contract/SVG CPU: eight actual traces of 25–56 samples, 50 warmups then 500 iterations per operation on Node v26.1.0. Mean contract construction 13.5–35.3 microseconds; mean PLAN_XZ/ELEVATION/ISOMETRIC_3D SVG string generation 15.4–47.8 microseconds. This excludes store reads, browser layout/raster and native GPU. Receipt SHA `830ece56bba8dc955429b2242143d6285cf1d9d713adb6f87a48e96ca15864f3`.

## Native live overlay and separate channels: native-r14

Frozen LAB `4b5ae7c776792fbde92b5f8b3e28a7e6bf437c32`; run `run-20261003125541-bf283c61696e`; snapshot `snapshot-20261003125541-4b33b3c13d58`; runtime PID 18780. `motionOverlay:true` was explicitly armed. A prelaunch no-gravity Arrow with tiny initial velocity and zero damage exercised Projectile representation; this is not ranged combat acceptance. The r13 private world was preserved.

| Selection | SERVER position samples | Derived render receipts / submitted frames | Last cumulative mean CPU ns |
|---|---:|---:|---:|
| Arrow revision 1 | 72 | 13 / 1,300 | 97,489 |
| Zombie revision 2 | 68 | 17 / 1,700 | 30,732 |
| Villager baseline revision 3 | 55 | 22 / 2,200 | 32,515 |
| Villager path-only revision 4 | 62 | 22 / 2,200 | 27,737 |
| Villager terrain revision 5 | 73 | 23 / 2,300 | 29,747 |
| Selection cleared revision 6 | 0 | 0 / 0 | Not applicable |

Each drawing receipt's source IDs were verified against retained SERVER_ENTITY_STATE rows with matching session/run/snapshot/process/Arena/UUID/revision and world-time age at most 100 ticks. Counts refer to frames with geometry submitted through the actual Forge render callback, not pixels, GPU work or total FPS. `rawPixelsVerified=false` remains explicit. Render timing includes bounded cache/geometry/build/draw submission but excludes GPU/framebuffer/writer.

Path-only burst captured six PATH_SEARCH_STATE/PATH_SEARCH_RESULT rows and WINDOW_ENDED; no other channels leaked. Terrain radius 3/max 49 cells executed once for its selection revision, preserving queried ground separately from PathFinder evaluated nodes. Same-JVM JFR measured each separate 20-second mode; the path window includes time after the ten-second burst, and the terrain query is a one-shot operation, not continuous querying. One sequence is insufficient for causal cost attribution.

1,044 canonical records, dropped 0, queue 0, clean ACK, verified exit, EVIDENCE_COMPLETE; original 85/85 SHA matched. Canonical `0759171a1cac3a9735ef959dc524f886968717739173ead24cac6782925ca015`; finalization `4b4bfff9dbacdc58eb238197b4f4ab4237bad1147d7f3a8714012b3f985e1098`. JFR 9,997,351 bytes / SHA `45a546d929c754df858654fb407b08053405ba27b3b87e88f75dcce58ed55b58`; receipt SHA `ec8dc9d64858ab7962ab19bc3969b8308eef05f7bfda72f58bee36e9010c989d`.

## Default-OFF regression: native-r15

Frozen LAB `d7b880b584d7e1028f797378de9ec643583f4209`; run `run-20261003130528-90736b992b0b`; snapshot `snapshot-20261003130528-dd3053f5f626`; runtime PID 46732. Config omitted `motionOverlay` while private launch env supplied `KNEEKURA_DEBUG_MOTION_OVERLAY=1`. Core's explicit default forced the child to OFF. Arrow 32 and Zombie 31 position samples were retained; all render receipts were zero. Selected absent UUID produced actual SERVER_TARGET_TRACKED=false, observation `obs:forge-runtime:46732:193`; cleared selection produced no selected position/render rows.

219 canonical records, dropped 0, queue 0, clean ACK, verified exit, EVIDENCE_COMPLETE; original 85/85 SHA matched. Canonical `cb76671d1de2f257cff0619f19e62675431ef1b0435d52b158b1957d0e53c702`; finalization `689fa5ce4545ffe002a6712e94609b0b50dfef659d4b25271f3d08f12e1b9455`; report SHA `7f8637959b1265fccad8f1b467998e9819e3462912170a37a8ed661566ef266a`.

## Failure and repair history

Earlier r1–r5 startup/resource IO failures, r9 prelaunch guard and r10 Citadel synchronous experimental-confirmation/DirectoryLock failure remain retained; none is counted as a successful native run. Private confirmation metadata/resource cache fixes and prior Hydra Gson-null repair are documented in earlier dated reports.

The first native overlay compilation exposed an extra legacy level argument to the new Arena-preserving writer helper; signature correction and genuine full bridge compilation resolved it. Short absent-target intervals could still be connected when only position rows were considered: failing Java and Node tests reproduced this before the d7b880b correction. Both native cache and retained presentation now cite the explicit absent record as MISSING_SELECTED_ENTITY. Native r14 predates this narrow correction; r15 proves the newer generation's default-OFF and actual missing-target observation, while the short disappear/reappear boundary is covered by pure retained-source tests.

Private finalizer retries retained intermediate coverage/generated artifacts rather than overwriting final evidence; the corrected consumer excludes rows without a SERVER world gameTime. Native r13 actual CLI/Motion reads proved canonical/finalization SHA unchanged. All JARs, full bytecode/source dumps, worlds, screenshots, JFR and private logs remain outside Git.

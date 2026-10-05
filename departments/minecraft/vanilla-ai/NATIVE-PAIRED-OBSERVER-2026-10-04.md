# Native same-save observer and overlay comparison

Producer: `91b0ddc9255945972b2fe7d2acfc7e7f8757a0b0`, Minecraft1.20.1 / Forge47.2.0 / JDK17, genuine unchanged MOD53a84d0 and TF mapped artifact. Scope: **descriptive incremental path-hook/selected-overlay comparison**, not full section16 acceptance or causal equivalence.

## Initial state and design

Each of six independently launched trials restores all85 exact r24 post-setup/prelaunch save files and the same options SHA256 `eb71499d9e5c986e8edb4c4019e36dc0643260d81ce906186a3c842dae4c224c`. The uninspected baseline is preserved. Original official Tank85 hashes and control-v2 bytes remain unchanged; every predecessor world is retained. Private prelaunch setup is the actual-AI Zombie/survival player/52 fences of r24, not the original scene or resize acceptance.

Two order-reversed rounds are BASE→HOOK→OVERLAY and OVERLAY→HOOK→BASE. All arms retain the existing selected snapshot/bridge and the same JFR settings. BASE has deep hooks/overlay OFF, HOOK arms only the bounded path channel, OVERLAY adds the selected Motion renderer. This does **not** compare against bridge-free Vanilla or measure every channel. Warmup is10s, requested measurement9s; actual wall/CPU-boundary/tick intervals are retained separately.

## Observed values

Process busy cores are total user+kernel CPU seconds divided by that arm's actual CPU boundary interval. JFR JVM CPU fractions normalize against32 logical processors; they are a different measurement. GPU columns are two owned-PID3D-engine boundary utilization samples, not per-draw duration or a time average.

| Arm | Actual tick span in9s wall window | Process busy cores | JFR JVM user+system | GPU3D boundary samples | Original Path results in selected context | Latest in-window overlay CPU mean / frames |
| --- | --- | --- | --- | --- | --- | --- |
| 01-base | 40768..40938 | 3.404 | 11.306% | 23 → 22% | 0 | OFF |
| 02-hook | 40693..40873 | 4.770 | 15.832% | 12 → 18% | 4 | OFF |
| 03-overlay | 40696..40873 | 4.358 | 14.761% | 10 → 14% | 2 | 48.479µs / 900 frames |
| 04-overlay | 40688..40863 | 4.559 | 15.467% | 8 → 23% | 1 | 60.468µs / 900 frames |
| 05-hook | 40697..40872 | 4.496 | 15.456% | 7 → 21% | 2 | OFF |
| 06-base | 40698..40873 | 4.094 | 13.746% | 7 → 19% | 0 | OFF |

Hook-minus-BASE differences were1.366 and0.402 busy cores. OVERLAY-minus-HOOK was-0.412 and0.062. The differing signs/magnitudes, different readiness ticks and search/trajectory populations prevent attributing these differences solely to the observer or concluding negligible/zero effect. Overlay-reported CPU covers build/draw-submit only; GPU completion, writer and readback are excluded.

All six stores finalize EVIDENCE_COMPLETE with unique observations/drop0/queue0/cleanACK/verified exit. BASE has no original deep callback or overlay-status records; HOOK has no overlay records; both OVERLAY trials have actual render-status records. Absence of these records is not a claim of zero event-dispatch cost. The cache remains bounded/default OFF and raw Cardinal suppression remains enforced.

| Arm | Canonical observations SHA256 |
| --- | --- |
| 01-base | `59f78fde0afc9a90e7c9ffd84a6332b7cb0d75111cbd63e7ee07375bfd59077c` |
| 02-hook | `103be5b6be369152f43d949665c9032e4c9d8601f8c3f8af587db9d0f032bff3` |
| 03-overlay | `33b4b6163091d6fed97815d31ad37d1929a682773f0ffd22d467a7f4cac13868` |
| 04-overlay | `cf6e4126fc5f35aa49c50cbe6d9898f48cc51e0f8defaf95974ee103dd85f95a` |
| 05-hook | `e829cd10a3f50ece1336006f576d5318db62876de4f4f50f9dbdf0d0ec68db58` |
| 06-base | `27642d58668ad4081b10a367d6c2a202a21914f53694a0de99a0c52d1749245a` |

Private source: `C:/temp/kneekura-tech-remaining-data-20261004/paired-observer-r26/comparison-receipt.json`, per-arm JFR/source IDs/restore receipts. Static/derived exports never rewrite the finalized canonical bytes.

## Remaining performance coverage

Same save/options do not fix RNG, JIT, thread scheduling, ready-time AI progress or other-machine load. JFR and OS queries contribute overhead; samples can miss short work. Finite path bursts may end before later snapshots. Two rounds are insufficient for statistical equivalence or all-Mob/gameplay acceptance. Goal/Brain, malus queries, bridge-free/default-Tank, offline trace generation and plan/elevation/isometric render require their own matched measurements. GPU draw attribution and simultaneous related-projectile native rendering remain separate work.

## Separate native framebuffer diagnostic

R28 uses the same frozen producer with hooksOFF/overlayON and a private one-shot Forge event harness compiled from local source against151 existing hash-checked dependencies. It reads Minecraft's framebuffer through Screenshot.takeScreenshot at AFTER_LEVEL; it sends no keyboard/mouse input and changes no runtime camera/world state. Fixed camera90°/12° and the private lit fenced setup are set before launch. Readback+PNG IO is explicitly diagnostic-only and excluded from the six cost trials.

At client tick40568 (selection age133), one640×480 PNG SHA256 `60561f503d6ace14e68c752899769d829e04c00b854b65bd92dc36c71d79834f` was captured. Direct review shows blue/yellow and a faint red trail; fences occlude part of the trail. A palette diagnostic counts110 exact blue pixels and45 pixels within12 RGB units of yellow; old red fades with alpha and is not validated against opaque-red RGB. These counts do not uniquely attribute pixels to observations. Companion status `obs:forge-runtime:61388:143` /tick40571 is3 ticks from the image; its source list is temporal companion evidence, not exact per-pixel geometry provenance.

R28 finalized418 unique observations/EVIDENCE_COMPLETE/drop0/cleanACK/verified exit, canonical SHA256 `b3ca75cce0abdce92393c9849fe47cdd12465efcb62cd9cb4ff55fa034ad9da6`; original85 hashes unchanged. The first R27 harness attempt lacked pack metadata and stalled before READY; startup/heartbeat/predecessor/failure records are preserved with no clean writer ACK. R28 added private pack.mcmeta and then reached READY; this is a successful retry, not a claim that the prior screen's exact root cause was observed.

The R28 driver also omitted its private JFR settings: jcmd reported a settings parse error, so **R28 has no JFR recording**. Its exit status alone was not recording proof. The six separate R26 JFR recordings are intact. The diagnostic image is a private derived-presentation framebuffer, not registered raw Cardinal evidence or a new product capture API. All-camera/overlap usability, projectile age pixels and GPU draw timing remain unaccepted.

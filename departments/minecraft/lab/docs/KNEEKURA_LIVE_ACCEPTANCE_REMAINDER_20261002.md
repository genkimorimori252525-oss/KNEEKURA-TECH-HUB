# Remaining live acceptance — 2026-10-02

This record separates actual Minecraft observations, source contracts, visual interpretation and unavailable platform gates. All related PRs remain Draft. No merge/deployment or full production acceptance is established.

## Fixed baseline and implemented fixes

- Old-Golden native baseline TECH `2fb2e0eda62b2c132d53dc9d33c2fe1730475347`; MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`; LAB `a15c3c8621d6fba906b63e20bf5e1078649d37bc`. True-Tank image cohort uses LAB135563f; reviewed render-lifecycle fix is `6ed4831d6570415fe82ac518a6d3ba2d3adee506`. Later documentation/pin SHAs are separate from actual native run source identities.
- Paused capture now owns and restores both the renderer interpolation field and the independent Forge event interpolation cache. Raw metadata and strict comparison tolerances remain unchanged. CPU contract: 38 checks; related comparison/capture: 43; genuine Forge contracts: writer 3/image 6/Windows registered-world 73.
- A native owner-status filesystem failure formerly lost the useful Windows reason after truncating its long source/destination paths. The compact diagnostic records the deepest filesystem exception class/reason within the existing 256-character limit. No I/O retry or mutation retry is added.

## Actual matched control and repair

| Run | Native Cardinal-4 | Operations/reset | Stop/evidence |
|---|---|---|---|
| owner-r11 | 2 COMPLETE/RESTORED captures; all 8 raw partialTick values 0 | 2 bounded actions and reset VERIFIED | STOPPED / EVIDENCE_COMPLETE; drop 0, queue 0 |
| item-before | 2 COMPLETE/RESTORED captures; all 8 raw partialTick values 0 | 2 bounded actions and reset VERIFIED | STOPPED / EVIDENCE_COMPLETE; drop 0, queue 0 |
| item-after | 2 COMPLETE/RESTORED captures; all 8 raw partialTick values 0 | 2 bounded actions and reset VERIFIED | STOPPED / EVIDENCE_COMPLETE; drop 0, queue 0 |

The no-repair control is `MATCHED_EVIDENCE_ONLY / NOT_EVALUATED`. The actual repair adds only the missing registered `debug_force_takeoff` item model, following the existing sibling model and retaining the original texture. Native Before shows the missing-model checker; After shows the expected icon in north/east/west, while the south icon is NOT_VISIBLE. This is a bounded visual interpretation, not gameplay PASS. TECH retains both reports, hashes and a fresh-Store resume with no process launch or replay. Resource drift returns REVERIFY_REQUIRED/CURRENT_TARGET_CHANGED.

## Trigger attempt retained as failure

- `gravity-exit`: one support removal VERIFIED, but NoAI Reimu remained at y64/vy0 and produced no native ARENA_EXIT. Do not infer falling from NoGravity=false.
- The atomic status replacement failed; the original 256-character path-only message does not establish its Windows reason. Owner OUTCOME_UNKNOWN and cleanup UNKNOWN remain.
- Repeated watch did not add capture slots. Clean stop and seal retained 115 records with drop 0/queue 0. This does not make the event gate pass.
- A fresh declared Armor Stand fixture uses its actual SERVER_ENTITY_STATE: y64, vy=-0.0784000015258789, onGround=true, noGravity=false. Generic observation uses the six applicable native tick/tracking/state lanes; Maid AI/G2 lanes are NOT_APPLICABLE and their product gate is unchanged.

## Windows source verification

- TECH unfiltered full suite: **2,772 passed / 563 skipped / 92 failed / 48 errors / 10 warnings**, 425.48s. The 140 failed/errored entries are classified below. JUnit and complete logs remain private; no excludes or security-check weakening were added.
- Subsequent isolated authority/guard run: 853 passed / 9 failed / 2 errors. Node guard passed in this isolated run; the initial missing stdout failure remains unresolved rather than converted to success.
- Windows Thin Viewer contract: 6/6. Actual Edge/D3D11-WARP/WebGL deterministic framebuffer gate: 1/1, no skip. This is a browser replay test, not Minecraft runtime acceptance.
- LAB `npm run test:ci` remains incomplete where Windows symlink privilege blocks security fixture setup. The supported Linux source aggregate is checked separately at the final exact source pins.

| Classification | Failed/errored entries |
|---|---:|
| FIXTURE_DEFAULT_TEXT_ENCODING | 3 |
| CHECKOUT_CRLF_PINNED_SOURCE_HASH | 2 |
| FIXTURE_CRLF_SOURCE_BYTES | 3 |
| ENV_EXACT_JAVAP_API_UNAVAILABLE | 2 |
| FIXTURE_WINDOWS_ENV_SIZE_LIMIT | 6 |
| FIXTURE_NATIVE_PATH_SEPARATOR | 1 |
| ENV_SYMLINK_PRIVILEGE | 31 |
| UNRESOLVED_ORDER_OR_TRANSIENT_NODE_OUTPUT_ISOLATED_PASS | 1 |
| FIXTURE_POSIX_OS_CONSTANT | 2 |
| FIXTURE_POSIX_REGISTRY_OR_PLATFORM_GATE_PRECEDENCE | 37 |
| FIXTURE_LINUX_INPUT_ON_WINDOWS | 41 |
| FIXTURE_POSIX_EXECUTABLE_NAME | 1 |
| FIXTURE_LINUX_PROCESS_IDENTITY | 1 |
| FIXTURE_WINDOWS_SIGNAL_TERMINATION | 1 |
| FIXTURE_ZIPINFO_NORMALIZES_NATIVE_SEPARATOR | 1 |
| CHECKOUT_CRLF_PINNED_SOURCE_GUARD | 7 |

Windows CRLF checkout bytes in CelestialStaffItem.java hash to `0dbd7330306a3cd517658ef3e432c9cc8584ac21f69e878632305dd3edf5b5c8`; the read-only LF-normalized diagnostic hash is `4e190bf983d18946791a16f88f21eb48db037e7bdc9be8a0239af08137ab4b04`, exactly the pinned source constant. No source file or guard was normalized to manufacture a pass. POSIX registry/native-input fixture failures occur at the existing Windows rejection gates before the later Linux expectations.

Classification artifact SHA256: `3aa1f9513406075c69d024458e191d145511cca1d2e8d5b65054d73794d39d58`. Original unfiltered run is not rewritten.

## Material proof boundaries

| Field | Actual evidence | Remaining limit |
|---|---|---|
| Selected UUID and native position/health | Exact scoped SERVER_ENTITY_STATE / OBSERVED | No whole-world or behavioral equivalence |
| Main-class resources and container | OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE | Transformed live class bytes NOT_ESTABLISHED |
| Registered configuration bytes | ON_DISK_NOT_LOADED | Complete loaded/effective configuration NOT_ESTABLISHED |
| Selected model/texture resource artifact | Retained exact bytes plus native appearance | Full loaded resource-pack precedence/equivalence NOT_ESTABLISHED |
| Native camera/barrier/restoration | COMPLETE manifests and exact readback | Sequential four directions are not simultaneous frames |

The finite observation and native exit results are recorded below. True-Tank holding and the exploratory visual comparison have separate evidence below. Intentional interruption and final source CI are recorded only after they actually finish; none is inferred from source tests alone.

## Finite observation completed

`observe-30m-r2` ran non-owned observation for **1,800,014 ms**, 109 live PID/tick/subject samples, no actions or owner lease. It retained **5,062 canonical native records**, writer sequence 1–5062 without a gap, drop 0/queue 0. Clean stop ACK, STOPPED, EVIDENCE_COMPLETE, driver exit0, no failures. Exact selected Armor Stand SERVER state remained y64/vy=-0.0784000015258789/onGround=true. Report SHA256 `3ea2e2c0c8b2009b81e227b4911619f0c93aa79b74c4295af2695e7b247968ca`. Native record interval 2026-10-01T18:00:53.452546700Z–18:31:06.467642800Z; the required observation interval starts18:01:04.978Z after the generic native gate.

The initial wrong private Maid-G2 fixture attempt remains failed, clean stopped and sealed with61records. A transient C-drive low-space observation and separate auxiliary JVM startup-memory failures occurred during this shared-host session; they did not terminate the observed Minecraft process. They limit reproducibility claims. This single finite30min interval is not a production endurance guarantee.

## Native ARENA_EXIT established; timing window PARTIAL

Fresh `gravity-stand-r1`, request `5287fb2a968b9c0f835dff5581f314732368782d337ec892fbd8376ea5590606`, actual baseline `448ae0779f6f810378e1887796487f8ff0ba16846d0ca2b305ec01176beffb06`. One exact support-cell [2,63,4] was prepared under world lock from white_concrete to stone; other4095sectioncells unchanged/fullchunkreadback. One registered set_block support removal was VERIFIED.

Native event `obs:forge-runtime:30348:35`, SERVER/OBSERVED, `KneekuraDebugOwnerConnection.arena_exit`, at2026-10-01T18:35:21.702442500Z. Subject point naturally changed from [2.5,63.231523797587016,4.5] to [2.5,62.85489329934836,4.5]. This proves a sampled inside→outside point transition, not a general causal or combat claim.

| Offset | Actual coverage |
|---|---|
|-1000ms | MISSING / PRE_FRAME_NOT_RETAINED_AT_TRIGGER; the earlier manual capture is not substituted |
|0ms | One dispatched COMPLETE/RESTORED Cardinal-4 set, manifest observed+304ms; matched by dispatched ID within5s request window, not within250ms target tolerance |
|+500ms | Same retained set reused, observed-196ms relative to requested slot, within250ms tolerance; not an independent second capture |

Trigger window `trigger-13ddf411a593a7f715de733602f74feb`, outcome PARTIAL, sameFrame=false. Ring eviction5 is distinct from writer loss0. Window SHA256 `09e261a39744d4995de233e76f34072672a6aab04cbc4b95161ad8831dfbe01a`. Original manifest retains per-frame times and image lineage.

Read-only inspection did not arm the watch; explicit sealed watch completed WINDOWS_FINISHED. Repeatwatch returned OUTCOME_UNKNOWN and capture slot directories stayed exactly2 (manualslot0 plus dispatchedslot1). No slot2 was synthesized. The outside subject causes SUBJECT_NOT_EXACT_OR_OUTSIDE_ARENA; cleanup timed out and remains UNKNOWN, driver exit1. Safe stop still ACKed98records/drop0/queue0 and sealed EVIDENCE_COMPLETE. Whole failed-state world retained, then a fresh baseline copy is used for a different experiment. No uncertain mutation was replayed. Expiry/UNKNOWN/unloaded rejection is source-contract evidence in the19passing trigger tests, not a claim that a native unloaded entity was observed exiting.

## True-Tank presentation and holding cohort

The user corrected the true world to g3-real-machine-acceptance/reimu-mod/run/client_a/saves/KNEEKURA_DEBUG_WORLD. Old-Golden repair/exit/endurance evidence remains labelled as old Golden. Read-only shared-lock snapshot85files/11,613,055bytes matched pre/post/copy SHA256. Final originals recheck:85/85true-Tank and34/34old-Golden unchanged. Large copies/evidence live onK; earlierCprivate MOD copy is retained.

Actual g3 LAB8e36ea8 supports dimensions1..64/volume65536/origin change, unlike the initially inspected DownloadsLAB floor64/volume4096 implementation. Saved Tank19x11x19 at[0,224,0],OBSERVATION_BRIGHT,recipe e9ed87f3b512cf59dac3ce6eb0c08654d047657be1e383dc6df580a5582bcac3. Scoped fixture floor/pose/equipment/observer preparation occurs only in copies. Original resize/reset and YSM are not tested.

LAB135563f restores missing g3 grid/lightmap from an optional bounded SHA-bound ZIP capsule matched to saved geometry/current owner. No server lighting/physics/entity-effect changes. Actual tank-a-r7/tank-b-r3 raw images visibly restore grid and bright selected Reimu/staff. Each4COMPLETE/RESTORED sets,16raw partialTick0frames,6VERIFIEDactions/cleanup, clean stop/zero drops/queue/EVIDENCE_COMPLETE/driver0. Requests fdd176f9b132dc99d5b2ad0fe43d14c82eb0ba82b84a912e29ea8091be1b0498 / b9b955aa47cf5544240ad1a29fe522ca0abec47a0e2a55a8c516d943137b0a37; immutable native records/seals retained.

Blockbench thirdperson_righthand.translation.y6to4 preserves other model/display fields and texture. Strict comparison MATCHED_EVIDENCE_ONLY/NOT_EVALUATED/no reasons; generation/resource only declared differences. Comparison1340e21bc0c60a120cad62af0b77b73e6733f9fcecafcad87c3c5f16edde8532; paired sheet25f88736223c4cd6aebd1f69a597e252d3781f8645bce8903343914962f9c62e. Native staff shows small displacementN/E/W; south partly occluded. Registered numeric value is separate from observed appearance; exact loaded transform/aesthetic improvement/whole-scene equality unproved. Speech bubble differs.

Static tank-projectile adds one exact registered arrow, NoGravity/Invulnerable/velocity0. Two COMPLETE/RESTORED sets/eightframes,2VERIFIEDactions/cleanup, clean85records/zero drops/queue/EVIDENCE_COMPLETE/driver0. This tests visual occlusion/identity, not combat or flight.

Eight same-source cases have40A-E judgments/8F NOT_RUN in TECH visual benchmark. Implementer prepared/evaluated fixtures: exploratory/unblinded. Fresh reviewer independently inspected images/raw hashes/timeline order, not blind accuracy. Exact head mesh clipping AMBIGUOUS; RGB cannot prove numeric slot/exact UUID. Local contact-sheet-first recommendation leaves production default/provisional status unchanged. Native seals/canonical bytes and32exported raw hashes verified unchanged.

## Independent review and render-lifecycle fix

One fresh whole-branch reviewer:Critical0/Important1/Minor0. Cached view relied only on server ticks, allowing pause/expiry/server switch to retain grid/brightness. Fix6ed4831 guards both render consumers using original owner issued/deadline/server identity, clears on uninstall, requests native lightmap dirty recomputation on transitions including disconnect without level. No lease renewed. RED then GREEN30Tank checks(19recipe+11lifecycle), genuine Forge writer3/image6/world73, comparison/capture43passed. Windows portable owner suite fails existing symlink-privilege fixture after5Env checks; guard unchanged. Final Linux aggregate/post-fix native image recorded separately.

## Retained interruption startup attempts

Interruption-r2/r3 exceeded READY600000ms before owner/actions:0records/PARTIAL, no native interrupted action or mutation replay. Logs show forced full MOD compile(build.gradle compileJava outputs.upToDateWhen false) plus startup, not GC heap exhaustion. First private prewarm failed on shell-split Gradle argument; quoted-array correction is source-only/no owner/game. New finite trial requires genuine precompiled main source/classes/resources/refmap SHA verification, skips only verified main compilation. Normal build unchanged, actual LAB bridge compilation/handshake required. READY600s/owner120s unchanged. Private procedure is not a new public launch mode or loaded-target equivalence proof.

Final post-review native interruption/presentation outcome and exact pinned CI are indexed in the [TECH acceptance record](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/jolly/minecraft-mod-ai-assets-2026-09-28/departments/minecraft/mod-ai/LIVE-REPAIR-ACCEPTANCE-2026-10-02.md). That record distinguishes final native run source identity from later documentation-only commit identities and preserves UNKNOWN/NOT_RUN. Source-only genuine Gradle prewarm succeeded in7m12s; no game or owner was launched by the prewarm. This local record does not convert the retained startup failures into successful interruption trials.

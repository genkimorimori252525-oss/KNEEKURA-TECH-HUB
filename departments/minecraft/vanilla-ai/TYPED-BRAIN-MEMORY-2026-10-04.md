# Cached typed Brain memory — 2026-10-04

Scope: original sections5 B3 and15 scenario4. This is a verified implementation/native slice; the full goal remains active in the [execution matrix](REMAINING-EXECUTION-MATRIX-2026-10-04.md). TECH HUB is the source; LAB is its feature. Draft PR80 remains Draft.

## Cached facts and authority

Producer `52dca02183e547b5cb6d3838e247affdc99e798f` uses `TYPED_CACHED_MEMORY_V1` for exact WalkTarget, BlockPosTracker, EntityTracker and Path implementations. Entity subclasses are read only through source-verified base Entity cached fields. No tracker position/visibility query, custom getter/toString, new path search, eligibility, Schedule, Brain or behavior execution is invoked by this observation. The [additive source ledger](TYPED-BRAIN-MEMORY-BYTECODE-LEDGER-2026-10-04.json) retains six owners/21 fields with exact descriptor, class/disassembly/slice SHA and locator; ledger SHA `e9fd2bf8c7c1e2bdd763cccda5a79824af96817e804af092ca0988521bc28a60`. Original61-owner and R47 method-body ledgers are unchanged.

| Known value | Retained fields and limits |
| --- | --- |
| WalkTarget | Cached tracker, speed modifier, close-enough distance; no eligibility or Navigation result |
| BlockPosTracker | Cached block and center vector; directly constructed Vec3 keeps fractional values, unlike WalkTarget's Vec3-to-BlockPos constructor |
| EntityTracker | Cached entity reference and eye-height policy; no replay of currentPosition/currentBlockPosition/isVisibleBy |
| Entity | Base uuid, position, blockPosition, eyeHeight cached fields, irrespective of overridden getters; no claim of actual motion or query-time visibility |
| Path | Exact ArrayList cached nodes, next index, target, target distance, reached flag; prefix64 and known cached Node coordinate/type/malus fields, no frontier search or adoption |

Shared snapshot reference allocator remains capped at256, resets at targetRevision, and uses explicit memory/entity/path namespaces. It is separate from callback component identities. Existing goal identities remain unchanged. Exhaustion preserves cached facts with REFERENCE_LIMIT and no token. Null/nonfinite/unavailable fields, unsupported custom implementations/containers and truncated node prefixes remain explicit partial/unknown facts. Snapshot memory entries remain64, producer payload48KiB; consumer values8192, array64, object32, strings512, keys128 and total bytes64KiB remain bounded. Generic depth stays12; only tagged, separately validated typed-memory entry branches allow depth14 for a real WalkTarget → EntityTracker → Entity → point primitive. Unrelated deep structures remain rejected.

## Frozen native Villager trial

Private original-Tank copy, Forge1.20.1/47.2.0, pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`, actual installed producer above. Adult Villager UUID `55555555-6666-7777-8888-000000000001`, controlled survival player/support floor/glass/light/night-vision and modified health fixture; naturally advancing time, no seeded Brain memories or observer replay. This MOD-loaded trial is not pure Vanilla or an actual Tank resize acceptance.

- Session `sess-20261004075702-816fc85e3adb`; run `run-20261004075702-86595ab17025`; snapshot `snapshot-20261004075702-1005f8db77a5`; processEpoch1/ArenaEpoch0.
- Two30-second selection periods, revisions1/2 on the same exact subject; each has120 valid snapshots. Reference identities never connect across reselection.
- Revision1: WalkTarget65 /PATH63 /Look EntityTracker60. Revision2: WalkTarget83 /PATH70 /Look EntityTracker15. Each also has120 cached visible-player and120 targetable-player Entity references. These are repeated observation counts, not unique objects or successful actions.
- Same-snapshot known PATH/Navigation reference matches63+70=133; known snapshot references41/23 with zero identity-limit facts in this trial. Equality means only the same retained reference, not adoption, canReach, arrival or causal selection.
- Original callbacks: revision1 start-return191 /stop19 /tick-or-stop19 /Brain19 /Sensor8; revision2 start-return161 /stop25 /tick-or-stop37 /Brain24 /Sensor9. Each finite burst stops at256 events (120398/119352 payload bytes), even though snapshots continue. Later callback absence is not absence of original AI work.
- Sampled active state changes from core+idle at tick40428 (source21) to core+rest at40813 (source511); revision2 begins in core+rest. This is a sampled interval, not a recorded schedule trigger or activity-switch reason.
- Read-only drilldown retains78+71=149 memory-change intervals without query truncation; Motion retains74+83=157 actual samples. Overview byte limits omit the large brain_memory value explicitly while source IDs and bounded drilldown remain available. CANDIDATE/SELECTION/RESULT stay NOT_CAPTURED; callbacks/STATE/EXECUTION do not fill these stages. No native pixel/GPU acceptance is claimed.

## Failures, correction and verification

The first R48 process exited before READY: JDK17.0.12 native malloc failure in C2CompilerThread7 (Chunk::new), runtime PID58064/launcher13436, not a Brain observation failure. Fatal/replay/daemon-segment logs and failed world remain retained. An additive retry uses private runClient-only maxHeap1536m /ActiveProcessorCount4 /CICompilerCount2; no OS, global JVM, other application or pinned MOD source change.

The successful native output initially exposed a consumer defect:17 of240 snapshots with entity-backed WalkTarget exceeded generic depth12. The offending actual observation `obs:forge-runtime:38288:401` and failed finalizer are preserved. A regression first failed; consumer correction `5dcbef7` passes all240 without changing producer or rerunning the game. Five JS typed-memory tests,145 focused regressions and genuine all-bridge/Mixin API compilation, nine actual typed-memory/Gson interop cases and combined writer/owner/Arena/overlay contracts pass locally. Legacy snapshot tests also pass. Hosted producer checks ran144 tests/eight interop cases and pytest3149pass/332skip; these earlier checks do not cover the later correction. Final published HEAD CI must be verified separately.

Native canonical1,258 unique observations: SHA `1d9844365752036cb15ab818751382b8192dfa8ffc274762e33187d195d84f58`; EVIDENCE_COMPLETE finalization SHA `42e8d4ab5229a4a0a47801c20e59146abf5efa1397ad4469a549b601fce0ac2a`. Clean shutdown ACK finalWriterSeq1258/drop0/queue0; owned runtime38288/launcher48320 independently absent. JFR4,246,141 bytes SHA `586c969a65965df79972a3a0cf338fecba3d8361eabedcef606dcf9256ab9a29`. Original/control worlds and preserved failed predecessor/fixture baseline each85 files are rehashed unchanged. Private receipts remain under `C:/temp/kneekura-tech-remaining-data-20261004/native-r48-r2` and source/CI receipts under `typed-memory-r48-source`.

## Next boundary

Inspect concrete Villager registration, OneShot and Gate policy/child caller boundaries and MoveToTargetSink before adding missing original callbacks. Base Behavior does not cover independently implemented BehaviorControl. The typed target fields and reference matches alone do not establish eligibility, action adoption, complete activity-switch reasons or actual results. Full path comparisons/rejection/cost, broader Boss battles, matched observer CPU/GPU/images, live Tank resize, all section21 criteria and final whole-diff independent review remain open. Preserved Windows full-suite failures are separate from hosted Linux success; unchanged global encoding/permissions are not altered.

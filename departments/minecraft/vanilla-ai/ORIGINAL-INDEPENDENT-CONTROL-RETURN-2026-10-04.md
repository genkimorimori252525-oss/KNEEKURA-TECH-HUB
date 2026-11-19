# Original independent BehaviorControl returns — 2026-10-04

Original sections5 B3 and15 scenario4 continuation. TECH HUB is the sole source; LAB is its feature. Draft PR80 and the full goal remain active. This is a verified base-callback slice, not full causal Brain/result or all BehaviorControl acceptance.

## Source and implementation

Frozen producer `dbd695d771611509267c7533797a40d627f72dc2` adds required, noncancelling normal-RETURN injections for `OneShot.tryStart/tickOrStop/doStop` and `GateBehavior.tryStart/tickOrStop/doStop`. Existing Behavior methods remain unchanged. The recorder reads only the known base's cached status, class/reference identity and actual passed result; it never calls trigger, getStatus, debugString, children, eligibility, visibility, Schedule or AI again. It uses the existing Brain opt-in channel, selected reference, server thread, session/run/process/Arena/revision, event/byte/window and128-component identity gates. Event schema/kinds remain unchanged; reasonStatus stays NOT_EXPOSED. Unsupported independent controls stay outside coverage.

The [additive source ledger](INDEPENDENT-CONTROL-BYTECODE-LEDGER-2026-10-04.json) records18 same-artifact class identities,36 exact method locators and two status fields with descriptor/class/disassembly/slice SHA. SHA `960925e2e900daa2e82d5fff164218a5a212edc22d4ba8bd0725c9379bf87d83`; original61-owner, R47 and R48 ledgers remain unchanged. Locator presence is not a claim of complete package interpretation or loaded custom-Mixin semantics.

| Original body | Verified boundary |
| --- | --- |
| OneShot.tryStart | Calls trigger once; true sets RUNNING, false leaves prior status. A false result need not mean STOPPED. |
| OneShot.tickOrStop /doStop | tick unconditionally calls doStop, which sets STOPPED; both normal returns can occur in one tick. |
| BehaviorBuilder.create /$1.trigger | Constructs a generic OneShot wrapper. The resolved builder can return no Trigger before a concrete trigger executes; class name alone does not reveal which trigger or why false. debugString delegates to the builder and is not replayed. |
| Gate.tryStart | Required-memory checks, then parent RUNNING before policy. It returns true independently of child success. |
| ORDERED /SHUFFLED | ORDERED consumer is a no-op; SHUFFLED executes original ShufflingList mutation/sort. Observation never repeats it. Weight formula and full package population remain separate research. |
| RUN_ONE /TRY_ALL | RUN_ONE attempts STOPPED children lazily until first true; TRY_ALL attempts every STOPPED child and discards returns. Parent facts do not reconstruct child relationships. |
| Gate.tickOrStop /doStop | Ticks RUNNING children, stops when none remain; doStop sets parent STOPPED before child stops and exit-memory erasure. |
| RunOne | Inherits Gate bodies and configures SHUFFLED/RUN_ONE. Overrides that bypass observed base bodies are not covered. |

Villager registration separately selects baby PLAY vs adult WORK/JOB_SITE requirements; both configure core, meet/rest/idle/panic/raid/hide, default IDLE and an original Schedule update. Relevant core/rest/idle package locators and direct factory references are retained. This static registration is not the loaded runtime population or a reason assignment for opaque instances.

## Genuine regression and installed native evidence

RED failed after an actual OneShot trigger with the assertion that independent-control callback observation was missing. GREEN uses genuine originals and counters: no replay, false/true returns and cached state, same original exception, Gate true with failed child, RUN_ONE/TRY_ALL ordering, missing-memory rejection, custom status/debug/child guards,128-ref cap/known stability/reset, OFF/selected/thread/context/channel/time/event/byte fences. Compiled injection annotations and handler calls establish required normal returns without cancellation or lifecycle/getter invocation. Nine existing typed-memory and13 new actual Gson cases pass JavaScript validation. Capped identity is genuinely omitted by production Gson and normalized to unknown; candidate/selection/result are not manufactured.145 focused regressions and combined owner/writer/Arena/overlay/genuine all-bridge/Mixin API compilation pass locally. These untransformed tests are distinct from the following installed runtime proof.

Fresh private original-Tank copy, actual Forge1.20.1/47.2.0, pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`; precompiled8,444 files verified. Same labeled adult Villager/survival-player/light/support-floor/private fixture and natural day progression, no seeded Brain memories. Existing private runClient maxHeap1536m /ActiveProcessorCount4 /CICompilerCount2 budgets are retained after the preserved earlier R48 native malloc failure; no OS/global JVM/pinned MOD change. MOD-loaded scope is not pure Vanilla, paired observer-effect or actual Tank resize acceptance.

- Session `sess-20261004085111-46429589d3fd`; run `run-20261004085111-74641f7c8b1c`; snapshot `snapshot-20261004085111-50cba4710696`; processEpoch1/ArenaEpoch0.
- Same selected Villager `55555555-6666-7777-8888-000000000001`, two30-second periods with revisions1/2. Each has120 valid snapshots; all512 original callbacks pass the consumer contract.

| Original source method | Revision1 | Revision2 |
| --- | ---: | ---: |
| OneShot.tryStart.RETURN |105|138|
| OneShot.doStop.RETURN |7|9|
| OneShot.tickOrStop.RETURN |7|9|
| GateBehavior.tryStart.RETURN |13|2|
| GateBehavior.doStop.RETURN |13|2|
| GateBehavior.tickOrStop.RETURN |24|14|
| Existing Behavior.tryStart /doStop /tickOrStop |67 /6 /6|54 /8 /10|
| Brain.tick /Sensor.doTick |6 /2|7 /3|

All six new source methods have actual records in each revision. Examples are retained with source IDs in `native-r49/installed-control-proof.json`. OneShot totals275; Gate68. Sixteen known same-instance/same-game-tick OneShot stop-return→tick-return pairs retain both source IDs; no opaque trigger reason is inferred. Shared known callback references34/32 and zero unknown component-reference facts in these windows, distinct from snapshot-reference32/18. Native cap exhaustion is not claimed from the unit cap test.

Both bursts stop at256 events,122354/122738 payload bytes, before the complete200-tick allowance. More callback families now share the same finite budget; absence after cutoff is not absent gameplay. Sampled core+idle at40408 changes to core+rest at40813 outside the first finite callback window; generic OneShot true is not evidence of that Schedule trigger. Revision2 begins in rest.240 typed snapshots retain146 same-snapshot PATH/Navigation reference matches (71/75),150 memory-change intervals (84/66),167 actual Motion samples (83/84). Equality is not adoption/arrival; memory differences are not causal selection. CANDIDATE/SELECTION/RESULT remain NOT_CAPTURED. No native pixel/GPU proof or full observer-effect comparison is claimed.

1,324 canonical observations EVIDENCE_COMPLETE SHA `77f0dfea544f3a152c383fc6927acd93ce44695b220234df11ba5c058342949f`; finalization SHA `5450d639702f2b0d180d9fbf9a993f481a49c379498a203614961141d41998ec`. Clean ACK finalWriterSeq1324/drop0/queue0; owned launcher28504/runtime43256 independently absent. JFR3,733,273 bytes SHA `6d0b63714dbea50002c531d9a951a5dc4b792755ec8ad9df5830f137ab73fe7d`. Original/control/predecessorR48-r2/fixture baseline each85 files rehashed unchanged. Private receipts under `C:/temp/kneekura-tech-remaining-data-20261004/native-r49`; source extraction/RED/GREEN/CI and earlier private helper diagnostics remain preserved.

Producer CI37190254233(push),37190257936(source PR),37190257928(pytest) allSUCCESS. Actual PR checkout `23accb80d8d9007715924e6926e92d1b95b60b1c` has base57e52 and exact producer dbd695d parents; full LAB source suite,145 markers,13 control Gson cases, portable Java, pinned MOD compile/dependency/resource/unit gates verified. Hosted pytest3,149pass/332skip/8warnings242.68s. Final documentation HEAD checks are verified separately. Earlier Windows full-suite failures remain unresolved; hosted success does not erase them.

## Remaining original scope

Target original Brain activity-update/Schedule/caller and Navigation result boundaries with a capture window that includes the actual change; existing short callback prefixes cannot explain the later transition. Read concrete call/field/return semantics and prove no replay before any new hook. Parent-child relations, trigger identity, activity eligibility/reasons and actual results remain unknown where not directly captured. Full Vanilla/FRONTIER/community/source completeness, path comparisons/rejection/cost, wider Boss battles, matched CPU/GPU/images, live Tank resize, all section21 criteria and final whole-diff independent review remain in the [execution matrix](REMAINING-EXECUTION-MATRIX-2026-10-04.md).

# KNEEKURA Autonomous Debug Workspace v1

Status: DESIGN / implementation plan
Date: 2026-09-18 JST

Historical context: docs/KNEEKURA_LAB_HISTORY.md
Adversarial audit: docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_ADVERSARIAL_AUDIT_20260918.md

## 1. Decision

KNEEKURA-LABの主目的を、Web上へMinecraft/YSMを再現することから、「実Minecraftを検証機として使い、AIがその実機を観測・操作・再起動しながら自律的にデバッグできる作業環境を作る」ことへ変更する。

Minecraft real client/serverをworld state、entity execution、TLM behavior、YSM renderingのauthorityとする。外部側はCONTROL / OBSERVE / RECORD / COMPARE / AUTOMATEを担当する。Webは候補UIの一つであり、architectureの中心ではない。

## 2. Primary quality metric

第一の性能指標はFPSではなく Time To AI Ready とする。

    source change
      -> apply/restart
      -> Minecraft ready
      -> Probe ready
      -> Arena ready
      -> AI can run next experiment

T0 restart requested / T1 compile complete / T2 JVM started / T3 Forge initialized / T4 world load started / T5 player joined / T6 Probe connected / T7 Debug World ready / T8 DEBUG_READY を保存し、timeToAiReadyMs = T8 - T0 を測る。cold startとwarm restartは分離する。

## 3. Architecture

    AI
     |
     v
    KNEEKURA Control API
     |
     v
    Debug Orchestrator
     |---------------- Evidence Store
     |---------------- Human Workbench
     v
    Minecraft Debug Run
     |
     v
    KNEEKURA Probe
     |
     +-- World
     +-- Entity
     +-- TLM
     +-- YSM
     +-- Network
     +-- Performance

Minecraft画面自体をauthoritative visual outputとし、Workbenchに3D rendererを再実装しない。

## 4. Debug-only runtime

通常Minecraftを常時検証機にしない。専用working directoryを使う。

    KNEEKURA-LAB/debug-runtime/
      config/
      world/
      cache/
      logs/
      sessions/

通常プレイの.minecraftと分離する。Debug機能は kneekura.debug.enabled=true、専用run directory、valid debug session identity が揃った場合だけ有効にする。通常起動ではProbe/AI Control/experiment commandを停止する。

正式入口は human: kneekura debug start、machine: debug.start() とする。

Minecraft process restartとdebugSession endは別概念とし、OrchestratorはMinecraft再起動中も維持する。

## 5. Identity model

debugSessionId > runId > experimentId > actionId / observationId / traceId とする。

追加identityとして processEpoch / arenaEpoch / resourceEpoch / entityUuid / packetTraceId / renderTraceId を持つ。旧runと新run、reset前後、resource reload前後を自動吸着させない。既存tlm.sim.runとNetwork Companionのidentity disciplineを継承する。

## 6. Persistent debug world / resettable Arena

world全体を毎回作り直さず、小さなpersistent debug worldの内部にreset可能なArenaを置く。

初期preset:
- Narrow 9 x 7 x 9
- Normal 17 x 11 x 17
- Wide 19 x 11 x 19
- Custom

旧Water Tankの制約は理由なく継承しない。

Arenaは arenaId / arenaEpoch / origin / bounds / shape / environment / allowedMutationBounds / spawnPoints / baselineHash を持つ。AIのworld mutationは既定でallowedMutationBounds内だけ許可する。scenario.reset()でArenaだけbaselineへ戻す。

## 7. Typed Control API

AIはraw Minecraft commandやraw WorldEdit commandを基本APIにしない。

主な操作:
- world.inspectRegion / getBlock / setBlock / applyBlockBatch / fill / replace / clearRegion / restoreArena / buildShape
- entity.inspect / spawn / remove / teleport / setTarget
- scenario.reset / wait
- capture.snapshot / screenshot
- probe.configure / escalate / deescalate

内部backendはForge direct / Vanilla command / WorldEdit等へ交換可能にする。AI-facing contractを特定backendへ依存させない。

## 8. Observable information target

### Runtime identity
Minecraft/Forge/Java version、loaded mods、JAR hash、Git SHA、dirty state、diff hash、resource/model hash、dimension、process identity、debugSessionId/runId/epochs。

### World
block state、block entity、選択NBT/capability、collision shape、fluid、light、biome、time/weather/difficulty、loaded chunk、Arena geometry、region before/after diff。large regionやchunk/ticket診断は要求時のみ。全world常時scanは禁止。

### Entity
ID、UUID、EntityType、position/rotation/velocity、bounding box、health、attributes/effects、tags、owner/target、vehicle/passenger、ground/gravity/collision、alive/dead/removal reason、必要なinventory/equipment。

TLM-specificとしてmaid capability/state、task/work mode、combat、owner relation、spellcard state、意味が証明できたinternal stateを追加する。

### AI / navigation
active target、target change、running goals、goal start/stop、navigation、current path、path nodes、next node、recompute、move/look/jump control、distance、line-of-sight、cooldown、TLM section/mode/phase。

旧SimLabの「何を選んだかだけでなく、なぜ選んだかを残す」を継承する。ただし理由がコード上で証明できない場合は推測せず reasonKnown=false と observedInputs を返す。

### Combat
projectile spawn/owner/type/velocity/lifecycle、damage、attacker/direct source/damage source、amount、hp before/after、death/removal、knockback、必要なsound/particle。帰属精度を EXACT / CORRELATED / HEURISTIC / UNKNOWN で明示する。

### Network
既存Network Companionを継承・拡張する。packet send/receive、direction、class、safe scalar payload、process/thread、gameTime、packetTraceId、handler entered/completed、semantic milestoneを取得する。

Molangは M0 intent / M1 send / M2 receive / M3 handler / M4 dispatch / M5 consumed / M6 applied を分離する。

### YSM / Molang / animation
model identity/resource hash、target UUID、Molang intent/dispatch、M5/M6、relevant scalar runtime state、animation request、discoverableなcontroller state、render entered、YSM entered/completed、bone/palette snapshot on demand、model-to-world on demand、必要時のみfinal pose/final vertex evidence。

command sentとstate applied、render not observedとanimation not appliedを同一視しない。

### Client/render
client tracking、render eligibility、renderer/YSM entry-complete、camera/FOV、framebuffer、FPS、screenshot、必要時のみmatrix/final-vertex capture。

### Performance
server/client tick、render frame、selected subsystem timing、GC、memory、process CPU/memory、profiler artifacts。generic performanceは既存profilerへ委譲し、KNEEKURA独自instrumentationはTLM/YSM causal evidenceへ集中する。

### Failure
latest action/observation、last tracked state、exception/stack、crash report、relevant logs、network tail、Probe health、exit code、可能ならscreenshot、source/runtime identity。Minecraft crash後もOrchestratorがfailure bundleを作る。

## 9. Information limits

新水槽でも全情報は取得できない。以下を正式な限界として扱う。

1. API/hook/stable fieldが無いprivate/obfuscated internal state。
2. instrumentされていない分岐の「本当の理由」。入力と結果から推測できても観測とは分離する。
3. client未tracking Entityのclient-only state、unloaded chunkのruntime state。
4. GPU driver内部最適化やhardware schedulingの内部理由。
5. JVM/OS scheduler、JIT、GC、raceの完全な因果。観測自体がtimingを変えることもある。
6. filesystem/HTTP/native process等、Minecraft外の副作用。
7. 完全なdeterministic replay。seed固定でもthread/network/external time等で崩れ得る。

状態は OBSERVED / DERIVED / CORRELATED / INFERRED / UNKNOWN として epistemic status（情報の確からしさの区分）を持つ。NOT_LOADED / NOT_TRACKED / UNKNOWNを「存在しない」と混同しない。

## 10. Observation Architecture v2 — AI-first logging

旧水槽の良いログ設計を継承し、さらに改善する。

目標は「全部を常時表示・保存せず、必要な証拠を失わず、通常時は静かで、異常時やAI要求時だけ深くなる」。

### Preserve: delta logging
pos/phys/anim等は前tickと同じなら書かない。forward-fillで任意tickの状態を復元可能にする。

### Preserve: keyframes
一定期間変化がなくてもkeyframeを書く。途中参加readerの待ち時間に上限を置く。

### Preserve: silence heartbeat
何も起きていない時間とrecorder freezeを区別する。他eventが無い場合だけheartbeat/tickを出す。

### Preserve: event channels
damage/spawn/gone/network等の重要eventはdelta suppressionしない。

### Preserve: fail visibly
UNKNOWN / NOT_TRACKED / NOT_RENDERED / UNATTRIBUTED / INCOMPLETE を黙って補完しない。

## 11. Multi-level observation

### L0 Health
常時・極小コスト。process/tick/probe alive、tracked target、event rates、drop count、queue depth、last evidence age、Arena identity。

### L1 State Delta
通常Debug。対象UUID/Arena対象だけ。position、velocity、hp、target、AI mode、navigation summary、animation summary、重要TLM stateを変化時だけ記録。

### L2 Causal Events
goal start/stop、target change、path recompute、damage、projectile、packet、Molang milestone、render milestone、action receipt、exception。

### L3 Snapshot
AI要求時のみ。entity deep snapshot、nearby blocks、path nodes、capability、YSM scalar、inventory、selected NBT。

### L4 Deep Trace Burst
異常時/明示要求時だけ短時間。high-frequency navigation、packet detail、render matrices、YSM bone、thread/timing等。常時L4は禁止。

## 12. Ring buffer / pre-trigger capture

異常検出後だけ深く記録すると直前が失われるため、RAM上にbounded ring bufferを持ち、直近5〜10秒程度の高頻度eventを保持する。

crash、target gone、navigation stuck、M5 without M6、render lane stop、invariant failure、AI explicit capture等をtriggerに PRE-ROLL + trigger + POST-ROLL をEvidence Storeへ固定する。

## 13. Observation scopes

GLOBAL_HEALTH / ARENA / ENTITY_UUID / ENTITY_SET / REGION / PACKET_TYPE / SUBSYSTEM / EXPERIMENT を必須scopeとして使う。

通常は ENTITY_UUID + EXPERIMENT。全Entityのfull deep traceは明示的diagnostic operationに限定する。

## 14. Evidence Broker

AIへraw log streamを垂れ流さない。Orchestrator内にEvidence Brokerを置く。

主なquery:
- debug.status()
- entity.current(uuid)
- entity.changes(uuid, since)
- experiment.timeline(id)
- evidence.anomalies()
- evidence.explainGap()
- network.chain(traceId)
- ysm.chain(traceId)
- world.diff(region, before, after)
- performance.summary(window)
- evidence.deepDive(topic, window)

最初はcompact summaryを返し、必要ならdrill-downする。

## 14A. Observation != Conclusion

KNEEKURA TECH HUBのStaged Observation設計を新水槽へ取り込む。

Minecraftから得た事実と、AIがそこから作った解釈を同じrecordにしない。

    Runtime Evidence
      -> Observation
      -> Finding
      -> Hypothesis
      -> Conclusion

ObservationはMinecraft/Probeが観測した事実だけを持つ。

Finding以降はAIまたは解析器の解釈であり、必ず根拠となるObservation/Evidence IDを参照する。

例:

    observation:
      collisionAhead = true
      navigationActive = true
      velocity = 0

    finding:
      statement = "obstacle handling may be stalled"
      epistemicStatus = INFERRED
      evidenceIds = [obs:..., obs:...]

AIが生成したFindingやHypothesisを、後段のEvidence BrokerがOBSERVED情報として再提示してはならない。

## 14B. Immutable RunSnapshot

各run開始時に、再現性に必要な実行環境をimmutable snapshotとして固定する。

RunSnapshot候補:

- runId / debugSessionId
- Git commit SHA
- dirty flag
- working diff hash
- built class/JAR hashes
- Minecraft / Forge / Java version
- loaded mod IDs / versions / hashes
- TLM / YSM hashes
- config hash
- resource/model hash
- Arena baseline hash
- Probe version
- observation schema version
- FAST_DEBUG / CLEAN_VERIFY profile

run開始後に環境が変わった場合、既存RunSnapshotを書き換えずresourceEpochまたは新runを発行する。

古いPASS結果を、新しいsource/config/resourceのPASSとして扱わない。

## 14C. Re-verification / stale verification

KNEEKURA TECH HUBのupstream re-verification原則を採用する。

過去にPASSした修正やinvariantは、依存するsource/runtime identityが変わったら自動的に「現在もPASS」とみなさない。

verification recordは最低限:

- verificationId
- experiment/scenario identity
- RunSnapshot ID
- result
- evidence IDs
- verifiedAt
- dependency fingerprint

を持つ。

dependency fingerprintが変わった場合:

    VERIFIED_CURRENT -> REVERIFY_REQUIRED

へ移る。

過去のEvidenceは消さず、古い状態に対する歴史的事実として保持する。

## 14D. Evidence-backed cause candidates

Evidence Brokerは、原因を一つに断定する装置にしない。

原因候補はそれぞれ独立recordとして扱う。

    CauseCandidate A
      statement
      epistemicStatus
      evidenceIds
      conflictsWith
      missingEvidence

    CauseCandidate B
      ...

複数候補が残る場合はAMBIGUOUSのまま返す。

popularity、単なる相関、以前の成功例、AIの自信だけでwinnerを選ばない。

AIは次のexperimentで候補を潰す。

## 14E. Incremental derived-state computation

KNEEKURA TECH HUBで調査済みのSalsa / rust-analyzer / Tree-sitter系の増分計算思想をEvidence Brokerへ取り込む。

ただしv1でSalsa等の特定library導入を必須にしない。

目的は、入力が変わっていないderived stateを毎回再計算しないこと。

例:

    position changed
      -> invalidate distanceToTarget
      -> invalidate arenaContainment
      -> maybe invalidate navigationProgress

    YSM resource hash unchanged
      -> model identity cache remains valid

derived queryは:

- dependency inputs
- cached value
- source observation IDs
- invalidation reason
- computedAt

を持てる設計にする。

最適化は必ず測定後に行う。Evidence Brokerが十分小さい段階では単純実装を優先する。


## 15. Evidence lane health

旧Capture Health Lanesを一般化する。

各laneは count / lastAt / rate / lastSequence / dropped / errors / status を持つ。

主要lane:
SERVER_TICK / CLIENT_TICK / TARGET_TRACKED / AI_DECISION / NAVIGATION / PACKET_SEND / PACKET_RECEIVE / PACKET_HANDLER / MOLANG_M5 / MOLANG_M6 / RENDER_ENTERED / YSM_ENTERED / YSM_COMPLETED / ACTION_APPLIED / OBSERVATION_WRITTEN。

単一のstale=trueは禁止し、どこで止まったかを返す。

## 16. Provenance / completeness

重要field/eventに source / sourceSide / sourceMethod / identity / observedAt / epistemicStatus / completeness を持たせる。

deep probeは complete、visitBudget、visited、depthBudget、truncatedContainers、timedOut を返す。既存YSM Object Walkerのcomplete/negative contractを一般化する。not found + complete=false はnegative evidenceにしない。

## 17. Backpressure / perturbation control

logging自体がMinecraftを重くしてバグを作らないよう、bounded queue、async disk writer、drop counters、per-channel budget、payload limit、deep trace time limit、OBSERVATION_DEGRADEDを導入する。

lossy/losslessをchannel schemaに明記する。causal acceptanceで絶対に落としてはいけないeventだけdurable pathを選べるようにする。

## 18. Invariants / watchpoints

AIが毎tick全情報を読む代わりに、cheap invariantをローカルで監視する。

例:
- target UUID must remain tracked
- navigation active but speed == 0 for N ticks
- M5 must lead to M6 when supported
- entity must remain inside Arena
- render entered must lead to YSM completed
- packet send must lead to receive in local test

違反時だけanomalyを上げ、L4 burstをtriggerする。

## 19. Experiment timeline

experimentIdごとに hypothesis / baseline / action / actionReceipt / observation / anomaly / conclusion を束ねる。actionにはidempotency keyを持ち、再送による二重world mutationを防ぐ。

## 19A. Adversarial hardening requirements

敵対監査で、AI自律化では「派手な失敗」よりも「古い状態や不完全な操作を正しい証拠として静かに混ぜる失敗」が危険と判断した。以下をv1の必須条件へ追加する。

### Command fencing

全mutation requestは最低限:

- debugSessionId
- runId
- processEpoch
- arenaEpoch
- actionId
- idempotencyKey
- expected target UUID/region
- optional precondition fingerprint

を持つ。

Probeは現在identityと一致しないmutationを実行せず `STALE_COMMAND_REJECTED` を返す。

Minecraft再起動後にqueueへ残った旧run commandを新runへ適用してはならない。

### Verified action receipts

receiptを「backendが受理した」だけでSUCCESSにしない。

action lifecycle:

    REQUESTED
      -> ACCEPTED
      -> APPLIED
      -> VERIFIED

とする。

VERIFIEDは可能な範囲で実worldのpostconditionを再読して確認した場合だけ付ける。

例:

    world.fill requested
      -> backend executed
      -> affected region re-read
      -> requested block states match
      -> VERIFIED

部分適用はSUCCESSではなく `PARTIAL_APPLY` とし、実際に変更された範囲をreceiptへ残す。

### Arena reset fidelity

Arena resetはblock再配置だけでは不十分。

reset対象候補:

- blocks / block entities
- Arena-owned entities / projectiles / items
- scheduled block/fluid ticks where controllable
- temporary effects
- target ownership/task state
- scoreboard/team state used by scenario
- game rules if scenario mutates them
- time/weather if scenario depends on them
- forced chunks/tickets owned by KNEEKURA
- client-side tracked target state
- KNEEKURA Probe ledgers/ring buffers/caches
- YSM/TLM diagnostic state that KNEEKURA itself changed

各state classを:

    RESETTABLE
    PERSISTENT_BY_DESIGN
    EXTERNAL
    UNKNOWN

に分類する。

reset後にbaseline fingerprintを再計測し、期待baselineと一致しない場合は `ARENA_NOT_CLEAN` として次experimentを開始しない。

「resetできないstate」は隠さずRunSnapshot/experimentへ残す。

### Epoch fences for delta/caches

arena reset、process restart、resource reload、tracked UUID切替の境界では:

- delta ledger
- forward-fill state
- derived cache
- ring-buffer interpretation
- stale lane state

を新epochへ持ち越さない。

新epochの最初は強制keyframeを要求する。

### Cross-process ordering

server/client/Orchestratorのeventをwall clockだけで一本化しない。

各writerはmonotonic local sequenceを持つ。

cross-process causalityは:

- explicit trace ID
- packetTraceId
- actionId
- request/response identity
- known causal milestone

を優先する。

gameTime/wall clockはcorrelation dataであり、単独で因果関係を確定しない。

clock metadataとして process start、monotonic origin、wall-clock sample を保存する。

### Ring-buffer coverage truth

Deep Trace Burstは必ず:

- requested pre-roll
- available pre-roll
- requested post-roll
- available post-roll
- dropped count
- truncated
- trigger identity

を返す。

5秒要求して2秒しか残っていない場合、「5秒分取得済み」と扱わない。

### Probe perturbation budget

観測そのものが挙動を変える危険を計測する。

各Probe/trace levelに:

- estimated/observed overhead
- queue pressure
- dropped events
- capture duration
- enabled instrumentation set

を残す。

必要な不具合ではProbe OFF / normal / deep traceのcontrol comparisonを可能にする。

### Runtime attestation

RunSnapshotには「buildするつもりだったsource」だけでなく、実際に起動したruntimeをbindする。

最低限:

- loaded mod/JAR hashes
- classpath/build output identity
- Probe build identity
- resource/config hashes observed from runtime side

をProbe handshakeで返す。

Gradle cacheや古いmods directoryにより、AIが編集したsourceと実行bytecodeが違う事故を検出する。

### Supervisor isolation

Debug Orchestrator / watchdogは、デバッグ対象Modと同時にcrashする場所へ置かない。

Minecraft processが起動不能、Probe handshake不能、crash loopになっても、Supervisorは:

- processを停止
- logs/crash reportを回収
- last known RunSnapshot/actionを保存
- retry budgetを管理
- human/AIへfailure reasonを返す

ことができる。

無限restart loopは禁止する。

### Profile semantic parity

FAST_DEBUGとCLEAN_VERIFYでscenarioの意味を変えない。

WorldEdit、ModernFix、profiler等はbackend/helperとして使えても、scenario contract自体はそれらに依存させない。

helper有無で結果が変わる場合、その差をevidenceとして扱い、FAST_DEBUG PASSをCLEAN_VERIFY PASSへ昇格させない。

### Topology identity

Integrated Server / Dedicated Server / remote server等の実行topologyをRunSnapshotへ明記する。

network/threading挙動がtopologyで変わるため、異なるtopologyの結果を同一条件として自動比較しない。

### Incremental-cache safety

derived-state cacheはraw Evidenceの代わりにしない。

依存入力を完全に宣言できないderived queryはcacheしない。

cache hitでも参照元Observation IDsとdependency fingerprintを返せるようにする。

invalidation correctnessが未証明の段階では単純な再計算を優先する。

### Resource exhaustion

Evidence Storeのdisk使用量、ring buffer、queue、profiler artifactをboundedにする。

disk-low / quota exceeded時は `OBSERVATION_DEGRADED` または `EVIDENCE_STORAGE_EXHAUSTED` を明示し、証拠が欠けたrunを完全なPASSとして扱わない。

## 19B. Concurrency, source, and render-observation hardening

### Single-writer Arena lease

同一Arenaへのmutationは同時に複数実行しない。

Arenaは:

- arenaRevision
- activeExperimentId
- writerLeaseId
- leaseOwner
- leaseExpiry

を持つ。

mutation requestは `expectedArenaRevision` を含み、現在値と違えば `ARENA_REVISION_CONFLICT` で拒否する。

VERIFIED mutation/resetごとにarenaRevisionを単調増加させる。

複数AI/複数Workbenchはread-only観測可能だが、既定ではArenaごとにwriterは1つだけとする。

### Serialized action queue

同一experimentのmutationは順序付きqueueで実行する。

後続actionは前actionがVERIFIEDまたは明示的FAILEDになるまでworld mutationを開始しない。

parallelismが必要なdiagnosticは、独立Arenaまたは独立runへ分ける。

### Source workspace checkpoint

AIによるsource変更は復元不能な直接編集にしない。

debugSessionごとにisolated worktree/branchまたは同等のsource workspaceを使い、各変更前後に:

- base commit
- patch/diff
- source fingerprint
- compile result
- changeId

を保存する。

compile不能、Minecraft起動不能、Probe handshake不能になった場合でも、Supervisorから直前checkpointへ戻せる。

main/default branchへの直接自律書換えはv1の既定経路にしない。

### Build-before-restart gate

source変更後:

    edit
      -> compile/check
      -> runtime artifact identity produced
      -> restart
      -> runtime attestation
      -> DEBUG_READY

とする。

compile gateに失敗した場合、壊れたMinecraft起動を試みずcompile evidenceをAIへ返す。

### Arena recovery fallback

baseline fingerprint mismatchがresetで解消しない場合、同じArenaを使い続けない。

fallback:

1. reset retry (bounded)
2. fresh Arena region / fresh arenaEpoch
3. immutable debug-world templateからworld再生成

の順で復旧できるようにする。

scheduled tickやthird-party capability等、局所resetが安全に証明できないstateはfresh Arena/worldへ逃がす。

### Tick/condition-based waits

`scenario.wait` は単純なwall-clock sleepを主契約にしない。

条件例:

- wait N server ticks
- wait until entity state predicate
- wait until lane count advances
- wait until action postcondition
- wait until timeout

tickが停止した場合はtimeout理由を `TICK_STALLED` として返す。

### Render observation preconditions

YSM/render evidenceは、対象が実際にclientでrender対象になったときだけ得られる。

従って:

- TARGET_TRACKED
- IN_RENDER_RANGE
- FRUSTUM_ELIGIBLE
- RENDER_ENTERED
- YSM_ENTERED
- YSM_COMPLETED

を分離する。

`YSM_COMPLETED=0` だけでYSM故障と断定しない。

render-specific experimentでは `renderObservationMode` を明示し、必要ならdebug cameraを対象がrenderされる位置へ自動配置する。

camera automationがserver-side behaviorへ影響し得るtestではperturbationとして記録し、通常AI behavior testとrender observation testを分離する。

### Local control-plane transport safety

Control APIがHTTP/WebSocket等を使う場合でも「localhostだから安全」と仮定しない。

最低限:

- loopback bind by default
- per-session capability token
- mutationはGETで実行しない
- request body/schema validation
- action allow-list
- body/payload size limit
- browser UIを使う場合はOrigin/CSRF相当の防御
- stale/unknown session token reject

を要求する。

## 19C. Evidence consistency and crash-boundary hardening

### Evidence Cut / query consistency

Evidence Brokerは、別時刻の値を無印の「現在状態」として合成しない。

各queryは `evidenceCut` を持つ。

evidenceCutには少なくとも:

- runId / processEpoch / arenaEpoch
- per-writer lastSequence
- relevant gameTime range
- queryStartedAt / queryCompletedAt
- coherence mode

を含める。

coherence mode:

    ATOMIC_SNAPSHOT
    SAME_TICK_WHERE_AVAILABLE
    BOUNDED_SKEW
    BEST_EFFORT

複数laneをまたぐ回答でatomicityが無い場合、その事実をAIへ返す。

厳密なbefore/after比較が必要なexperimentでは、Probe snapshot barrierまたは同等の明示的capture boundaryを使う。

TECH HUBの「選択したClaimと説明したClaimが一致しなければfail closed」と同様に、query中にrun/epoch/target identityが変化した場合は古い選択結果を混ぜず `EVIDENCE_CONTEXT_CHANGED` で失敗させる。

### Mutation effect envelope

要求したpostconditionが成立しただけでは、余計な副作用を見逃す。

mutation actionは可能な範囲で:

- intended region/entities
- allowed side effects
- before fingerprint/diff
- after fingerprint/diff
- unexpected changes

をreceiptに残す。

要求領域が正しくても許可外のblock/entityが変化した場合は `VERIFIED_WITH_UNEXPECTED_EFFECTS` またはFAILとして扱う。

### Crash-during-action recovery

Minecraftがmutation途中でcrashした場合、そのactionをSUCCESS/FAILEDの二値で推測しない。

`OUTCOME_UNKNOWN` とする。

restart後は:

1. stale command reject
2. durable action ledger確認
3. Arena baseline/fingerprint確認
4. 必要ならreset/fresh Arena
5. 新experiment開始

を行う。

部分変更されたpersistent worldをそのまま次experimentへ引き継がない。

### Durable idempotency ledger

idempotencyKeyの記録はメモリだけに置かない。

少なくともdebugSessionの寿命中はdurableに保存し、Orchestrator/Minecraft reconnect後にも:

- already VERIFIED
- PARTIAL_APPLY
- OUTCOME_UNKNOWN
- never seen

を区別できるようにする。

同じkeyでpayloadが違うrequestは `IDEMPOTENCY_CONFLICT` として拒否する。

### Invariant epistemic boundary

watchpoint/invariant violationは「バグ原因」ではなくObservation/Anomalyである。

各invariantは:

- invariantId
- version
- scope
- trigger predicate
- required inputs
- evidence IDs
- confidence/limitations

を持つ。

invariant自体の誤設計がAI conclusionへ昇格しないよう、Anomaly -> Finding -> Hypothesisの境界を維持する。

### Optimization cannot bypass evidence gates

Time To AI Readyを短くする最適化は:

- runtime attestation
- Arena cleanliness
- Probe handshake
- required lane health
- RunSnapshot creation

を省略して達成してはならない。

`DEBUG_READY` は速度指標ではなく、これらminimum correctness gatesを通過した状態名とする。

## 19D. Reproducibility and evidence-finalization hardening

### Randomness contract

「同じscenario」は同じ名前だけで定義しない。

可能な乱数sourceについて:

- world seed
- scenario-owned RNG seed
- KNEEKURA action RNG seed
- target Modが公開するseed/state
- experiment repetition index

をRunSnapshot/Experimentへ保存する。

target Mod内部やthread timing等でseed/stateを固定できない場合は `NONDETERMINISTIC_SOURCE_PRESENT` を明示する。

非決定的scenarioでは単発PASSを修正成功の十分条件にせず、同一条件の複数trialと結果分布を保持できるようにする。

「再現しなかった」と「直った」を同一視しない。

### Reproduction strength

experiment resultは最低限:

    REPRODUCED
    NOT_REPRODUCED
    FIX_VERIFIED
    REGRESSION
    INCONCLUSIVE

を区別する。

FIX_VERIFIEDには明示的acceptance predicateと必要trial数を持たせる。

AIの「見た感じ直った」をFIX_VERIFIEDへ直接昇格させない。

### Tick-liveness / pause semantics

Autonomous run中にMinecraft/integrated serverがUI、focus、pause state等で静止しても「バグ」と誤認しないよう:

- server tick advancing
- client tick advancing
- game paused
- screen/menu state where observable
- focus/pause configuration

をL0 Healthへ含める。

DEBUG_READY中にrequired tick laneが停止した場合は実験時計を進めず、 `RUNTIME_PAUSED` / `TICK_STALLED` として扱う。

### Evidence finalization

run/experimentの証拠は「ファイルが存在する」だけでcompleteとしない。

終了時にfinalization manifestを作る。

manifest候補:

- run/experiment identity
- artifact list
- size/hash
- last sequence per lane
- dropped/truncated counts
- writer errors
- clean shutdown / crash
- RunSnapshot ID
- observation schema versions
- finalizedAt
- completeness status

正常finalizeされたbundleだけ `EVIDENCE_COMPLETE` とする。

crash/truncated JSONLは価値あるEvidenceとして保持するが `EVIDENCE_PARTIAL` と明示する。

### Evidence-store authority

AIはEvidence Storeのcanonical artifactを直接書き換えない。

Minecraft Probe/Orchestratorが生成したraw Evidenceはappend-onlyまたはcontent-addressedに近い扱いとし、AIのFinding/Hypothesis/Conclusionは別recordとして追加する。

過去EvidenceをAI conclusionに合わせて書換える経路を作らない。

### Acceptance predicate provenance

acceptance predicate自体にもidentity/versionを持たせる。

同じ名前のtestでもpredicate定義が変わった場合、旧PASSを新predicateのPASSとして再利用しない。

## 19E. Trusted observer / oracle boundary

自律AIが「合格するように測定器を変える」ことを防ぐ。

### Trusted Computing Base

少なくとも以下をtarget-under-debugとは別の信頼境界として扱う。

- Debug Supervisor / Orchestrator core
- canonical Evidence Store writer/finalizer
- action fencing/idempotency implementation
- acceptance predicate registry
- evidence schema validator
- CLEAN_VERIFY用のtrusted observer/probe build

これらのidentity/hashをRunSnapshotへ記録する。

### Source edit scope

AI source-edit actionは明示的なallowed source rootsを持つ。

通常のbug fix sessionでは、target Mod sourceを編集できても:

- Supervisor
- Evidence finalizer
- acceptance predicate
- trusted CLEAN_VERIFY probe
- immutable scenario baseline

を同じ権限で変更できないようにする。

変更が必要な場合は「debug target change」とは別のinfrastructure changeとして扱う。

### Observer-change invalidation

FAST_DEBUG中にProbe/instrumentation自体を変更した場合、その変更前のverificationと直接連続したtrusted PASSとして扱わない。

observer identityが変われば:

    REVERIFY_REQUIRED

にする。

CLEAN_VERIFYではpinned trusted observer buildを使うか、新observer自体のacceptanceを先に通す。

### Oracle integrity

AIがacceptance test/predicateを変更してから同じtest nameでPASSさせることを禁止する。

verificationは:

- acceptancePredicateId
- acceptancePredicateVersion/hash
- scenario hash
- trusted verifier identity

をbindする。

predicate変更後は別verification generationとして扱い、旧失敗を「修正済み」と上書きしない。

### Evidence/Conclusion privilege separation

AIはFinding/Hypothesis/Conclusionを追加できるが、raw Evidence、RunSnapshot、finalization manifest、trusted verification resultを直接上書きできない。

これにより:

    AI interpretation != measurement authority

を構造として維持する。

## 19F. Debug-environment contamination guard

修正対象コードが「KNEEKURA Debug中だけ動く修正」になることを防ぐ。

### Target patch dependency check

通常のtarget Mod bug fixでは、patchが新たに:

- KNEEKURA debug-only API
- `tlm.sim.*` / `kneekura.debug.*` 等のdebug property
- FAST_DEBUG専用helper Mod
- debug-only world/scenario identity

へ依存していないかをchange auditで確認する。

明示的にdebug infrastructureを直すtaskでない限り、この依存追加はwarningまたはreject対象とする。

### CLEAN_VERIFY observer-only influence

CLEAN_VERIFYでは、可能な範囲でdebug systemの影響を「観測・scenario setup」に限定し、target behaviorを変えるhelperを除く。

RunSnapshotに:

- loaded helpers
- behavior-changing helpers
- observer-only helpers
- debug properties visible to target

を記録する。

FAST_DEBUGとCLEAN_VERIFYでtarget behavior条件が変わる場合は、その差を明示し同一verificationとして扱わない。

### Normal-runtime parity check

重要fixでは、必要に応じて追加のNORMAL_PARITY profileを持てる。

目的は:

> KNEEKURA自律操作を外しても、修正対象コードが通常runtimeで成立する

ことの確認。

NORMAL_PARITYは必ずしも全案件で必須ではないが、debug-only dependencyが疑われる場合のescape hatchとする。

## 20. Restart strategy

変更をLIVE / RELOAD / RESTARTに分類する。

LIVE: world/entity/scenario/observation config。
RELOAD: reload可能なresource/data/config。
RESTART: Java、Mixin、registry、network bootstrap等。

v1はHotSwapに依存しない。まずFast Restartを完成させる。

## 21. FAST_DEBUG / CLEAN_VERIFY

FAST_DEBUGは高速反復用で、startup optimizationやdiagnostic mod、profiler integrationを許容する。

CLEAN_VERIFYは最終確認用で余計なbehavior-changing helperを減らす。

修正成功は原則 FAST_DEBUG PASS + CLEAN_VERIFY PASS。

## 22. Existing assets

Retain/evolve:
runId/scenario、SimCh、SimDelta、heartbeat、Network Companion、M5/M6、YSM scalar probe、complete/negative contract、UUID exact tracking、schema validation、attribution quality。

Optional/legacy:
Viewer。

Regression/research:
Render Pack、Golden Oracle。

Primary live pathから外す:
LivePalette Web rendering、Capture Camera、Web YSM renderer。

## 23. Implementation gates

G0 Boundary Freeze: current inventoryとprimary/retained/legacy/research分類。
G1 Debug Launch: dedicated debug session/run identity、registered development workspace、一操作起動、exact Debug World direct join、Probe handshake、runtime attestation、DEBUG_READY、startup timing。
G2 Observation Core: L0-L2、Evidence Broker、lane health、delta/keyframe/heartbeat、UUID、provenance/completeness、epoch fence、cross-process ordering、ring-buffer coverage truth。
G3 World/Entity Actions: typed actions、Arena bounds、Arena baseline creation/verification、command fencing、VERIFIED receipts、partial-apply detection、idempotency、reset fidelity、baseline fingerprint。
G4 Deep Diagnostics: L3/L4、ring buffer、anomaly trigger、network/TLM/YSM deep probes。
G5 Fast Restart: compile/restart orchestration、isolated persistent Supervisor/Orchestrator/world、runtime attestation、automatic reconnect、stale-command rejection、restart-loop budget。
G6 Autonomous Debug Loop: reproduce -> inspect -> hypothesis -> experiment -> mutate -> observe -> source edit -> restart -> verify。
G7 Clean Verification: clean profileで再現し、source/runtime hash付きevidence bundleを残す。


### G1/G3 readiness boundary

G1の `debugWorldReady` は「Supervisorが指定した専用singleplayer worldへ入り、client/player/integrated serverが安定し、runtime identityが確認できた」ことだけを意味する。

これはArenaの清浄性を証明しない。

Arena geometry、mutation bounds、baseline fingerprint、reset completenessを含む `arenaBaselineVerified` はG3で追加する。G1がArena完成を名乗ってはいけない。

## 24. Non-goals v1

Web 3D renderer、Minecraft rendering完全再現、YSM Web再実装、常時full-world scan、常時full-entity deep logging、無制限packet dump、無制限reflection、AIのarbitrary shell access、HotSwap依存、完全deterministic replay保証。

## 25. Design rule

Observe cheaply by default.
Escalate only when needed.
Never hide uncertainty.
Bind every important fact to identity.
Let Minecraft remain the visual authority.
Make the AI spend its attention on the bug, not on log noise.

# KNEEKURA MOD shared debug system — deferred product-wide roadmap

**Decision date:** 2026-10-09
**State:** ACCEPTED DIRECTION / RESEARCH AND IMPLEMENTATION NOT STARTED.
**Owner system:** TECH-HUB existing Minecraft MOD-AI + LAB; **not** an additional stand-alone debug service.

## Owner's intent

Design one coherent diagnostic, observability and experiment system for KNEEKURA-created mods, initially:

- `Kirby_mod` → new canonical product folder `departments/minecraft/projects/kirby-mod/` after migration
- `NaturalGhastmod` → independent project, ghast AI/flight/barrage
- `reimu-mod` → planned later integration, Reimu AI/Molang/animation

Legacy per-mod debug commands, ad-hoc text dumps and the Kirby `/tlm` implementation are incomplete and non-canonical. During source migration preserve them for compatibility and provenance but **do not duplicate, extend or accept them as the shared debug system**. Replacement/deprecation must be gated by feature-equivalence proof and migration tests.

## Reuse — audit before building

The TECH-HUB repository already has:

1. `departments/minecraft/lab/debug-workspace/`: Supervisor, run/session/source identity, READY/runtime attestation, bounded capture, exact target UUID, server/client lanes, exported evidence and action controls. Its README includes historical milestone paragraphs: the 2026-10-02 current handoff supersedes those old status passages.
2. `departments/minecraft/lab/bridge/tlm-forge/`: product-specific probes and trace data; extract generalizable *adapters/contracts* without importing TLM assumptions as universal semantics.
3. `departments/minecraft/mod-ai/`: SourceSnapshot, TaskContext, test/evidence and editor integration; do not create a second knowledge store, authority layer or artificial observation.
4. Existing Water Tank trajectory/decision observability plans; reconcile with their current status and retain all run-bound provenance.

Start with a capability/gap inventory per module. Do not rewrite working G1/G2/G3/arena/tank adapters on speculation.

## Proposed shared interface — not implemented

Define a versioned, low-overhead event envelope from an optional Forge-side adapter to one LAB intake:

- `schema_version`, `producer_mod_id`, `event_kind`, `logical_side`, `mc_tick`
- `session_id`, `run_id`, `process_epoch`, `build_hash`, `source_hash`
- optional exact `dimension` / `entity_uuid` / ability or attack ID / `correlation_id`
- `capture_mode`, `sample_rate`, `dropped_count`, `evidence_status`, typed `payload`

Do not assert a causality claim merely because two timelines line up. Keep raw observations, derived findings and controlled interventions separate; use existing LAB run IDs and fences.

Suggested lanes, each opt-in:

- **Mob AI:** decision/state/goal ownership, candidate rejection, navigation and target selection, recent state transitions.
- **Combat/physics:** attacks, projectiles, collisions, knockback, movement trajectory and ability ownership.
- **Visual:** GeckoLib or YSM animation/state, model variant, Molang/pose and authoritative vs client-render discrepancy.
- **Networking:** packet type/direction, sync boundary, server authority, receipt and stale-state warnings.
- **Performance:** tick/MSPT, per-entity cost budgets, spikes, heap / allocations, drop counters.
- **Operations:** build/version mismatch, config, dependency errors, server/client warnings and structured crash metadata.

Product-specific fields remain namespaced extensions: `kirby.*`, `ghast.*`, `reimu.*`. No one-size-fits-all AI decision template; a common envelope is not a universal behavior model.

## Research and evidence admission gate

Research broadly in GitHub source and commit/issue repair histories, official Forge and Minecraft engineering documentation, established diagnostics/profiler code, specialized articles, and community reports (including Reddit). Score proposals for **specificity to Forge 1.20.1**, observed implementation, reproducibility, throughput impact, false-positive risk, side separation, test support, and maintainability. Reject attractive but unsupported claims.

Initial external sources to evaluate:

- Forge 1.20.x [events](https://docs.minecraftforge.net/en/1.20.x/concepts/events/), [logical/physical sides](https://docs.minecraftforge.net/en/1.20.x/concepts/sides/) and [Debug Profiler](https://docs.minecraftforge.net/en/1.20.x/misc/debugprofiler/) (anchor references).
- [spark](https://github.com/lucko/spark) and its [tick-loop guide](https://spark.lucko.me/docs/guides/The-tick-loop) (performance profiling reference; do not blindly vendor its implementation).
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/) (consistent event names and attributes; **not** a decision to depend on the full SDK).
- [Reddit example of intermittent modded Forge 1.20.1 client/server join NPE](https://www.reddit.com/r/ModdedMC/comments/1gun0o2/) — **anecdotal failure-mode hypothesis only**; use to create reproducible client/server regression scenarios, not to attribute arbitrary crashes to a named mod.
- More community solutions may be added with exact post/commit date and validation outcome; popularity is not proof.

Exclude by default: full-world scans every tick, unlimited entity/per-tick log streaming, undefined private-reflection hacks, crash-only retrospective guesses, unconditional packet payload capture, remote arbitrary command/script execution, and automatic actions based solely on AI interpretation. Production/developer worlds must remain separated.

## Design / execution sequence for later session

1. Pin latest TECH-HUB, LAB and all three product source snapshots. Inventory all legacy debug code, events, commands, instrumentation and what actually works.
2. Build a strict capability-gap and source-evidence matrix; score and prune community suggestions; specify typed schema and compatibility strategy.
3. Specify sampling/backpressure/ring buffers, access permissions, safe shutdown, sensitive-data redaction, monotonic ordering, client/server join and false-causality handling.
4. Build one smallest Forge 1.20.1 adapter and run-bound LAB test using a disposable debug world; derive a baseline for measurable profiler overhead.
5. Add Kirby, Ghast, Reimu adapters separately, with independent semantics and opt-in lanes. Retain temporary compatibility with legacy `/tlm`.
6. Validate fixture tests, exact UUID target isolation, event loss markers, server vs client discrepancy, repeatability, intentional fault injection, performance and multi-MOD coexistence.
7. Decide a documented promotion/deprecation migration only after passing parity checks. Do not remove legacy probes prematurely.

### Completion criteria

- One shared API/event contract and one observation/evidence workspace, versioned and documented.
- All three mod adapters provide needed state/AI/combat/visual evidence without a duplicate per-mod debug *system*.
- Explicit source→build→runtime↔observation linkage and distinguishable NOT_RUN/PARTIAL/PASS results.
- Demonstrably bounded overhead and memory in declared game scenarios, with no data leakage or privileged command expansion.
- Tests for inter-mod interference, client-server synchronization and backward compatibility.
- Unresolved findings remain UNKNOWN, never a manufactured PASS.

**No runtime implementation or acceptance is claimed by this planning record.**

## 2026-11-11 統合改訂：検証ルーター、人間の確認負担、Asset/Animation Method Registry

**改訂判断:** 既存の共通 MOD デバッグ構想を拡張する。既存の「Owner's intent」～「Completion criteria」は削除・縮小せず、以下を **横断的な実装・受入条件** として追加する。この文書が「検証と人間の分担」の正本であり、[VFX Studio v1.1 PLAN](2026-11-05-vfx-studio/PLAN.md) がモデル/アニメーション/VFX 制作の具体的な provider・format・実装順序の正本。[VFX監査](2026-11-05-vfx-studio/AUDIT.md) は双方のリスクと負例を保持する。原案（2026-10-09）時点の「未実装」は歴史的状態であり、実装の現在値は各 source と受入記録で都度確定する。

### 8. 追加の設計決定と権限・範囲

1. **水槽は検証手段の一つであり、デフォルトではない。** 実 Minecraft の再起動、長時間の capture、4方向撮影は費用のある副作用。AIの作業手順に「毎変更後に水槽」を固定しない。
2. **最も安価で、当該主張を立証できる手段を先に使う。** source/contract → schema/asset validator → unit/fixture/build → GameTest（Minecraft server起動を伴う）→ 対象を絞った実client/Water Tank → 人間が必要な意味・審美判断。これは厳密な全順序ではなく主張別に選ぶ。実機でしか証明できない項目を単体テストのPASSへすり替えない。
3. **人間の作業は低頻度・短操作・必要な判断に限定**する。AIは準備、対象配置、状態固定、装備/実験セット、録画、候補比較、復元、証拠整理を可能な限り事前に行う。人間にコマンド入力・環境復旧・UUID指定・不要な再試行を求めない。
4. **モデル・テクスチャ・リグ・アニメーション・VFXの制作方式は別々に選択・履歴保存**する。途中で方法を変えてよいが、元候補や変更理由、互換条件、取得元権利を失わない。最終セットは再現可能な参照/hashで結ぶ。
5. 新たな独立DB、常駐専門エージェント、一般MCPの自動登録、無条件のAI自律起動、通常Minecraft saveへの干渉は追加しない。既存 MOD-AI TaskContext/Store、LAB run/owner/arena、Evidence/CAS、Failure/Repair History を再利用する。
6. この改訂は **設計のみ**。外部 repo の導入・依存取得・実クライアント起動・本番改変・PR merge の許可ではない。

### 9. Verification Router（既存 TaskContext/adapter 上の軽量ポリシー）

**入力**: 対象モジュールとsource/build/resource hash、変更箇所のimpact set、主張(assertion domain)と成功/失敗条件、現存する証拠と鮮度、許可済みrunner/予算/検証時間、費用(起動時間・I/O・ログ量・人手)。**出力**は「試験候補」と明示理由であり、権限を付与するものではない。

| 証明したい主張 | 第一候補 | 実機へ進む条件 | 人間の役割 |
| --- | --- | --- | --- |
| JSON/リソース参照/モデル形式・ボーン名/UV範囲 | schema + static validator + exporter readback | 実描画でしかわからない問題が残る | 原則不要 |
| Javaメソッド・分岐・計算・再現可能な契約 | unit/fixture/build + 対象bytecode | 実際のGoal/packet/transform結果が論点 | 原則不要 |
| Blockbench geometry/texture、静止時の外観 | editor screenshot(同一camera) + invariant/UV check | インゲーム装備/描画・遮蔽・RenderType固有の主張 | 必要なら比較画像で一回選択 |
| キーフレーム/骨格階層/クリップの連続性 | animation validator、時刻指定のeditor frames | Controller/Molang/同期/描画時姿勢の挙動が未証明 | 自然さ・迫力などだけ |
| Mob AI の追跡/ターゲット/経路/状態遷移 | unit + GameTest + bounded decision event trace | path実移動/衝突/クライアント同期/不安定な動作 | 原則不要、遊びやすさのみ |
| VFX server cue、寿命、停止、FX位置 | cue tests、限定runtime trace | 画面効果・骨格追従・視覚上の重なり | 演出上の良し悪しを必要時に判断 |
| ゲーム内の楽しさ/演出の好み | 準備済み比較画像/短い動画、必要ならDebug Wand | 本人がゲーム内の操作感を指定した場合のみ | 2択/3択、OK/修正、任意コメント |

**判定の最小記録 (VerificationDecision v1案、実装済みJSONではない):**
```json
{
  "schema_version": 1,
  "claim_id": "animation:dragon:attack:bone_reference",
  "assertion_domain": "asset_structure",
  "selected_method": "offline_asset_validation",
  "alternatives": ["blockbench_preview", "tank_client"],
  "reason": "bone paths and keyframe shape are fully testable off-line",
  "tank_decision": "SKIPPED_WITH_REASON",
  "human_decision": "NOT_NEEDED",
  "evidence_refs": ["sha256:..."],
  "untested_domains": ["ingame_visual", "runtime_sync"],
  "result": "PASS_WITHIN_DECLARED_SCOPE"
}
```

**最小アルゴリズム**: (a) 証明対象を型付きで特定 → (b) 既存証拠の identity・hash・freshness・scope を検証 → (c) 同じ断言を最も低コストで検査する候補を選ぶ → (d) 未証明の残件だけを次の階層へ送る → (e) 結果と省略理由を記録。AIの「自信がある」だけでは省略不可。

**水槽起動の前提**: 何を証明するか／既存証拠ではなぜ不足か／対象UUID・tick・scenario・新規に取得するchannelは何か、の3点を記述。起動は既存の registered authority + budget + owner/live attestation が必要。**起動権限がない時は BLOCKED**、その場で許可を創作しない。

**過剰実行の停止**: 同じ source/build/resources、scenario、assertion、instrumentation、run前提、再現性契約の下で等価な新証拠が得られない反復を拒否。単純な「同一seedなら実行禁止」ではない。確率的挙動・race・flaky再現は独立試行が必要なことがあるため、統計目的、試行数、停止基準、budget を明示すれば複数回可。失敗時に同じ副作用commandを盲目retryしない。動的状態変化・新しい症状は別根拠として認める。

**省略の可視化**: `SKIPPED_WITH_REASON` は `PASS` ではない。別に `NOT_RUN` / `NOT_ESTABLISHED` を保持する。ソースにない新しいステータスを正本へ直書きせず、導入時は既存schemaとの整合・移行を設計する。

### 10. Mob AI を水槽の優先用途にする — 因果とログの分離

既存 [Entity Decision Observatory](../lab/docs/superpowers/plans/2026-10-02-entity-decision-observatory.md) を正本とし、Vanilla Goal/Brain/Path、MOD custom state-machine/utility/flightを同一の強制構造にしない。**実際に計測した** `INPUT → STATE → CANDIDATE → EVALUATION → SELECTION → EXECUTION → RESULT` の部分集合だけを表示する。

- **低コスト既定**: 対象を一体に限定した target/goal/state/path/cooldown 変化、結果イベント。常時スクリーンショットや全tickフルダンプはしない。
- **イベント起点の拡張**: 達成できなかった攻撃、経路中断、ターゲット喪失、一定時間停止などが起きた時のみ有限ring bufferと短いDecision Burstを取得。実測がない「canUse拒否理由」を捏造しない。
- **主なログ欄**: exact UUID+dimension、logical side、selected target、goal/brain state、path ID/node index、canUse/canContinue（計測できた時のみ）、同期境界、server tick、client/render clock、実速度・衝突・damage outcome、source/adapter/capture provenance、drop count。
- **分析出力**: 根拠を伴う状態遷移表＋失敗したassertion＋追加が必要な最小probe。視覚地図は必要なROIでのみ追加し、ゲーム画面の目視をAIの一次的な因果証拠にしない。
- **負例**: Goalが選択された=移動成功ではない、時間的前後=因果ではない、CLIENTの見た目=server authoritative outcomeではない、1回の試行=確率的仕様の証明ではない。
- **予算**: 保存サイズ、対象数、最大tick、sampling頻度、捕捉失敗/drop、instrumentation overheadをscenario毎に有界化する。性能未測定なら軽量と主張しない。

### 11. Human Review Assistant（自動準備・最小操作）

人間には審美・操作感・ゲームとしての面白さの評価を集中させ、構造・座標・セーブ復元・参照不整合は原則AI/機械が担当する。

- **0操作を優先**: 画像だけで十分なら、比較同一cameraの静止画または短い録画を生成して提示。人間が都度Minecraftを開く必要はない。既存render/captureが無い場合は取得の費用判断を先に行う。
- **ワンクリック/キー案**: disposableデバッグワールド専用の `KNEEKURA Debug Wand`（名称は案）。所有済みrecipeを元に、選択された1体だけを idle→walk→attack→VFX→reset の有限シナリオに切り替える。必要なteleport、装備、ボーン/エフェクト事前確認、背景・照明・録画はAIが準備。
- **確認依頼**: 人間へ「今回見るべき点」「A/Bどちらがよいか」「OK/要修正」だけを短く示す。自由コメントは任意。直感の個人差をAIの品質閾値へ勝手に変換しない。
- **負担管理**: 複数の審美レビューは重複を減らして束ねる。画面操作、ワールド再起動、mod導入、リソース修復、細かなコマンド入力、実験後片付けを人に頼まない。人間の回答待ちを理由に自律的に同じテストを反復しない。
- **安全**: Debug Wand は有効な debug session/owner/lease/arena内でのみ動作、通常ゲームでは無効。既存権限を超えるコマンド、任意 script、production save mutation、無限エフェクトは不可。人間がボタンを押してもセッション権限を昇格させない。
- **成果物**: human reviewがあれば screenshot/video refs、選択肢、結果、対象build/asset hash、確認日時/見た条件/未検証範囲をEvidenceに追記。未回答は `PENDING_HUMAN_REVIEW` というproposal状態として扱い、ゲーム動作PASSへ昇格しない。

### 12. Asset/Animation Method Registry（既存 CAS の参照レコード）

モデル生成・モデル変換・テクスチャ作成・リグ生成・アニメーション作成・VFX作成は **別のroute selection**。主な候補・権利・能力の詳細は [VFX Studio PLAN §8–9](2026-11-05-vfx-studio/PLAN.md) に保持する。

- **候補のID**: `img2blockbench.direct`, `img2blockbench.mesh`, `img2blockbench.img2threejs`, `mosaicary.gltf`, `blockbench.direct`, `blocksmith.experimental`, `animation.keyframes`, `animation.import_retarget`, `animation.procedural`, `vfx.photon_candidate` など。IDは将来契約案であり実装名ではない。
- **各選択を記録**: `asset_family`, `stage`, `method_id`, `reason`, `alternatives_considered`, `input/output SHA-256`, `provider revision/license`, `format+version`, `quality checks`, `runtime constraints`, `human review`, `switch_from`, `switch_reason`。
- **切替は合法**: AIは自分で方式を変えられるが、candidateをimmutable保存し、分岐・棄却・rollbackの因果関係を追う。再生成/再UV/再rig時に過去のanimationを黙って流用しない。bone path/hierarchy/pivot/bind/axis/clip依存の互換検査が必要。
- **最終セット**: model + texture/atlas + rig + animations(clip毎のmethod可) + VFX cues + profile/runtime target + provenance + validation matrix を **一つのmanifestで参照**。成果物の正本は既存 CAS であり、新たな資産DBを作らない。
- **報告**: 開始・重要な方式変更・完成時だけ人間向けの短い制作報告を表示。毎回のパーツ編集を通知しない。詳細なmethod historyは要求時に閲覧する。

### 13. 共通デバッグ×VFX×モデル制作の実装順序

| 段階 | 作業 | 受入証拠（欠けたら NOT_RUN/UNKNOWN） |
| --- | --- | --- |
| D0 既存能力再監査 | main/PR/モデルguard/Forge OBS/Entity Decision Observatory/VFX/Cardinal-4/Asset docsの実装状態と現行仕様確認、他作業差分との衝突整理 | exact source map、機能別 IMPLEMENTED/PLANNED/NOT_ESTABLISHED |
| D1 Verification Router | 変更影響・主張→最小検証方法の決定、明示省略、証拠再利用、実験起動前の3点説明 | 同じ変更で不必要な水槽を回さないfixture、必要なlive試験を省略しない反例 |
| D2 Method Registry | route selection、候補比較・切替、immutable候補、骨格互換、最終bundle | img2blockbench と Mosaicaryの切替時に旧候補を保持し、final manifestが検査可能 |
| D3 Animation Asset | GeckoLib 4対応、骨格・クリップ・controller・effect timingの検証、編集部品だけ更新 | 静的/編集プレビューPASSと runtime未証明を分離 |
| D4 Mob AI observability | 既存shared event envelope + Decision Observatoryの選択的adapterを1種類追加 | 失敗したgoal/path/targetのevent→result、false-causality負例、overhead/drop |
| D5 Human review | 既存UI/短いキャプチャを優先、必要時だけ Debug Wand 最小権限を追加 | 1操作の有限演出再生、整合性・復元と未回答の扱い |
| D6 統合実証 | static item→rigged mob→VFX付き攻撃の順で必要性が立証された工程のみ実機へ | 同じ入出力での作成方式記録、適切な検証選択、人間の負担、runtime結果の区別 |

**合格の定義**: 低コスト検証で決着した事案の不要な再起動回数を減らしつつ、真に実機が必要なケースの検出率を落とさない。起動回数だけを最適化して、根拠のないPASSや見落としを増やしてはならない。性能・時間短縮・人間の操作数は同一課題のbaseline対比で初めて報告し、事前に数値を作らない。

### 14. 実装時の監査・停止条件（追加）

- 既存PR #114 のVFX設計/監査、並行branchを更新する際、未マージ・未実機の主張を完成済みと書かない。複数の「最新計画」を新規作成しない。
- `img2blockbench` の画像1枚から隠れた面や厳密な骨格を確定したと主張しない。素材の出所・使用条件/商用条件・画像→3D providerの送信先/課金条件を記録。
- `Mosaicary` のURLインストールはアップデートが自動で発生し得るため、使用するpluginの固定コピー・hashを使い、任意のダウンロード/アカウント/Sketchfab tokenはデフォルトで使わない。
- Code/Scheme testだけで GeckoLib実描画やYSM状態適用をPASSにしない。逆にUVやJSON参照の修正だけのために毎回水槽を起動しない。
- 新しいMCP、plugin、VFX providerを複数常駐させない。見つけたrepoはまず読取専用で比較、採用できる最小機能だけ既存adapterへ統合する。
- 既存履歴や検証証拠を削除/上書きしない。レコード追加はすべて source/build/run/assetのidentityに紐付け、未検証は未検証のまま残す。

**改訂の状態:** DESIGN PROPOSED / IMPLEMENTATION NOT STARTED。既存の限定的なBlockbench+staffと実水槽の試験成果はその範囲のまま保持する。Code・CI・本番ワールド・登録権限はこの文書更新だけでは変わらない。

### 15. 制作AIの改善余地とAnimation Providerの統合（2026-11-11）

**本章は既存のD0–D6の置換ではなくD2/D3/D6の具体化。** VFX PLANの [§9 Animation Provider Selection](2026-11-05-vfx-studio/PLAN.md) が導入候補、機能の選別、実装手順S0–S6を定義し、同じディレクトリのAUDIT Gが負例を引き受ける。仕様を3つの別計画書に増殖させず既存3文書の役割を維持。

1. **編集経路の重複を禁止:** sosadly + TECH HUBの現行Blockbench guardのみをデフォルトのwriterにする。adhiは第一にGeckoLibの独立read-only validator、jasonはanimation skill/補間API調査、Renasは実測で不足した手続きIK/接地アルゴリズム、Blender Skillsは特殊ケースのbake。既存の同等機能を再実装したりMCPを複数常駐させない。
2. **AIの改善権利:** clip制作・補間・部分修正・方法選択・検証fixtureは、同じ規定の範囲内でAIが理由付きで変更できる。上流の新候補や改善案を研究・提案でき、実証で優れていれば選択候補に昇格できる。ただしprovider導入/権限/課金/外部送信/公開/本番影響、明示不採用の復活を勝手に承認しない。
3. **不採用の固定:** Kimodo と video2mocap は今回の制作パイプライン、PoC、隠れたfallbackから除外。既存モデル生成・Mosaicary変換・GeckoLib・VFXの確定した候補は勝手に消さない。
4. **再実験の合理性:** Verification Routerは起動回数を数える門番ではない。モデル/animation/JSONは静的/Editorで確認し、controller/Mob AIの実動作は必要な実機で証明。実機を何回実施するかは「残る主張・新しい証拠・試験設計」に従う。一律の固定起動上限を追加せず、現行の安全なrun権限/時間・CPU/保存予算と停止条件を遵守する。現実に確率試験が複数回必要なら、実験ごとに有限予算を宣言する。
5. **Human Review:** AIがコマンド/ワールド/装備/動画/復元を準備する。人は自然さ、好み、ゲームとしての感触だけを短い画像比較/任意のDebug Wand等で判断する。人が不在のときは「未評価」であり、AIが勝手に最終承認しない。
6. **記録:** animation authoring と format transfer と runtime playback を別方法としてMethod Registryに結ぶ。clip単位の途中切替、旧候補、bone/pivot/coordinate conversion、easing/effect loss、GeckoLib version、source/asset/run、人手評価を最終Asset Method Manifestに参照する。すでにあるStore/CAS/Historyを拡張するので別台帳・別DBを作らない。
7. **自己改善の実証:** 人工的なbone不一致やclip loop不連続を与えたとき、AIが自ら最小の修正手段を選択し、before/after比較で改善を証明し、変更理由・失敗・未知を記録できるか確認。人間が途中で全作業を逐一指示しなくてもよいことを受入に含める。

**状態**: 既存ソースにない機能はDESIGN ONLY、製品級の実装/Windows/新provider接続/自己改善成功はNOT_RUN。既存の限定的な静的モデル受入を一般化していない。

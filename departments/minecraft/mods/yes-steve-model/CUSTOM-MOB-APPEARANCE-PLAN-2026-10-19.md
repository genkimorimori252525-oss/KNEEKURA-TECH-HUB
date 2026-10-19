# 自作MODのモブへYSMモデルを表示する接続方針

## 目的と到達点

ユーザーの2026-10-19の最終指定は「自作MODのモブにYSMモデルの見た目を使えれば十分」。モブの種類は未定。全難読化の解読は目標にしない。今回は静的解析のみで、実装・コンパイル・ゲーム起動・表示成功は未確認。

固定対象：YSM 2.6.5 Forge MC1.20.1、原本JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`。調査基点は `c3c5b76b362e92d3fddf906383db97e142ac11ef`。読みやすい型名は意味対応ラベルで、安定した公開API名ではない。公開source候補と配布物全体の同値性は未確定。

**結論：非PlayerをYSMで表示する既存経路があり、自作モブ用の小さな連携層を作る根拠がある。** Touhou Little MaidのEntityMaidを元のEntityのまま表示する実装が手本になる。任意のプレイヤーモデルが全アニメーション込みで無変更動作する保証はない。

## 最小構成

通常の `Mob extends LivingEntity` 系を当面の前提とする。

1. **自作EntityTypeのclient renderer登録**：自作モブ自身の描画入口からYSMを呼ぶ。バニラ全体のdispatcher差替えは不要。
2. **個体ごとのYSM wrapper**：本来のモブを保持し、model ID・texture・アニメーション状態を管理する。AI、ダメージ、移動、当たり判定は元モブが所有する設計。描画フレームごとのwrapper作り直しや別個体間の可変状態共有を避ける。
3. **YSM本体のmodel読込み・geometry・Molang・native描画を利用**：通常のアクセス条件を保持する。モデル復号、別形式への書出し、プレイヤーへの偽装は前提にしない。
4. **モブ用controller**：最初は待機・移動・被弾・死亡など必要な状態だけを既存モデルのanimationへ結ぶ。攻撃など独自動作は自作モブの状態に明示対応させる。名前や存在を仮定せずモデルごとに確認する。
5. **未準備時のfallback**：YSM未導入・無効・モデル未読込時には自作モブ本来の描画へ戻す設計。client専用classの分離、個体破棄・world切替・model再読込時の寿命管理を含む。

種類・モデルは未定なので、特定のゾンビ・ガスト等を実装対象として固定しない。まず再利用可能な接続契約を確立し、対象決定後に一種類・一モデルで実装する。マルチプレイで個体ごとの見た目を揃える場合は、entity識別とmodel ID/texture等の同期を追加要件として扱う。

## 原本に基づく拡張境界

ownerの接頭辞はすべて `com/elfmcys/yesstevemodel/`。

| 意味対応 | 原本owner・境界 | 確認した内容 |
|---|---|---|
| AnimatableEntity | `o0000OoOooO0oo0o0oooo0Oo` | 原本Signatureの型上限はEntity。Player専用ではない。 |
| CustomHumanoidEntity | `o0O0oOooOo0OoOo0oOo00O00` | public abstract、型上限LivingEntity、protected constructor `(LivingEntity;Z)V`。 |
| GeoReplacedEntityRenderer | `OOoo0o0oO000ooO0Oo00OoOo` | public abstract、public constructor `(EntityRendererProvider.Context)V`、public humanoid描画入口がある。選択したtexture描画本体はLivingEntityへcastする。 |
| Controller setup | 上記wrapperの継承hook `a_()V` | protected abstract。モブ対応のcontrollerを構築する必要がある。 |
| Resource-holder factory | `oOo00OoOO00O000ooO0Oo00o.o0OOooo0o0OO00OoOOOo0o0O(ClientModel;Z)` | protected abstract。対応するholderを返す必要がある。 |

既存原本snapshotのYSM継承階層にある8個のabstract宣言をname+descriptorで解決すると、新wrapperに残るhookは上記2つ。geometry getter、texture、scale等はhumanoid側に具体実装がある。Minecraft外部親クラスを含む全コンパイル要件を確定したという意味ではない。

humanoidのpublicモデル更新入口は `Oo0Oo0o00O00Oo0OOoOOoooo(String;String)V`。既存の更新処理を通し、内部fieldへmodel IDを書くだけで済ませない。基底rendererはvanilla PlayerModelを描画の補助として生成するが、元EntityをPlayerへ変換する処理ではない。

## そのまま流用してはいけない部分

- **PlayerMainPredicate**：原本owner `ooOoOOO00OO0OO0ooOOOo0Oo` の選択したpredicateは、bytecode offset 4でCustomPlayerEntity、10でMinecraft Playerへcastする。汎用モブwrapperをそのまま渡せない。
- **PlayerControllerCollection**：factoryの原本BootstrapMethodsにもCustomPlayerEntity型のcallbackがある。Consumerの型消去を理由に全factoryを共用しない。
- **具体maid/player renderer**：maidのEntity版bridgeはoffset 2でEntityMaidへcastする。専用rendererのインスタンスへ自作モブを直接渡さず、汎用基底から自作用入口を作る。
- **player専用Molang入力**：確認したvariableの型検査不適合はboxed Integer 0、function側はnullを返す。必ずクラッシュするわけではないが、プレイヤー依存の表示条件やアニメーションは意味が変わる。モデルの必要入力を「そのまま使える・モブへ対応付ける・未対応」に分ける。
- **vehicle経路**：一般LivingEntityも扱えるが、専用モデル定義・初期化済みcapabilityが条件。既存playerModelを任意モブへ指定する万能設定とは確認できない。

## 静的な根拠と限界

新たな限定確認では原本13 ownersから14 methodsを再抽出し、既存の命令・operand・handler・code hash記録と照合した。factoryの27 BootstrapMethods記録も一致。generic Signatureは原本classfileから確認。これらの件数は完成率ではない。中央669件のmapは変更しない。独立semantic reviewは今回未実施。

主要な既存資料：

- [Maid entity bridge](MAID-ENTITY-CONTROL-RECOVERY-2026-10-17.md)
- [Maid capability / renderer](MAID-RENDER-CAPABILITY-RECOVERY-2026-10-17.md)
- [Maid controller registration](MAID-CONTROLLER-REGISTRATION-RECOVERY-2026-10-17.md)
- [Render selection / humanoid wrapper](RENDER-SELECTION-RECOVERY-2026-10-17.md)
- [Model readiness / resource holder](MODEL-READINESS-SCOPE-RECOVERY-2026-10-17.md)
- [Player controller assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md)
- [Dispatcher routing](DISPATCHER-RENDER-REPLACEMENT-RECOVERY-2026-10-17.md)
- [Pipeline overview](YSM-PIPELINE-REUSE-HANDOFF-2026-10-18.md)

作者の[メイド1.2.0更新記録](https://gist.github.com/TartaricAcid/119473335ab0654d7eb3f9611a84b68a)にもYSM描画対応がある。ただしその記録の対象YSMは2.4.0であり、今回2.6.5の正確なシンボル確認の代用ではない。

## 次の実装前確認は必要部分だけ

1. 固定2.6.5向けadapterの正確なdescriptor、nested holder access、開発環境の名前変換・再難読化を確認する。安定APIとして将来版対応を約束しない。
2. resource-holderの設定値、model readiness、個体ごとのwrapper保存/破棄を確定する。
3. モブ用controllerを組み立てるための最小コンストラクタ／登録契約を確定する。PlayerMainPredicateを通さない。
4. 対象モデル決定後に、そのモデルの必要query・animation名・texture条件だけを照合する。

静的解析で接続可能性と必要な実装範囲は絞れた。**連携MODが完成した、ゲームで描画できた、全YSMモデルと互換であるとはまだ言えない。** 現在のユーザー方針に従い、実起動やForge問い合わせは進めない。

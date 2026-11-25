# 移植規則カタログ v0
初期対象 Forge 1.20.1 ⇄ NeoForge 1.21.1。全規則は CANDIDATE / STATIC_ONLY / HUB_RUNTIME_NOT_RUN。原典は [SOURCES](SOURCES.md)。逆方向は設計候補でありModPorterの検証結果を流用しない。
## 索引
| ID | 対象 | 種類 | 根拠 |
|---|---|---|---|
| P01 | build・metadata・Java | loader + vanilla | S3 |
| P02 | registry / event | loader + vanilla | S1/S2 |
| P03 | ItemStack NBT / components | vanilla | S1/S2 |
| P04 | networking | loader + vanilla | S1/S2 |
| P05 | Capability / attachment | loader | S2 |
| P06 | rendering, mixin, worldgen, resources | 調査必須 | S2 / 元先実装 |
## P01 — 開発環境
Forge Java17 + mods.toml、NeoForge 1.21.1 Java21 + neoforge.mods.toml。MDKの固定版から build/gradle properties/runの差を参照。元のmod id、version、依存条件、mappings、resource processing、Mixin/ATを保つ。逆移植ではJava21専用API・言語機能をJava17に戻すか等価実装。ビルドツール変更は必須ではない。テスト: clean build、JAR metadata、依存解決、client/server。両MDKの実ビルド未実施。
## P02 — Registry / event
Forge RegistryObject<T> → NeoForge DeferredHolder<R,T> など（R=registry base, T=concrete subtype）。逆は対象の登録方式へ戻す。イベントは正確な型とbus、side、発火条件、キャンセル挙動を照合。単純な全パッケージ置換は禁止ではなく不十分。
S1 [RegistrySourceBoundaries.kt](https://github.com/CrabMods/modporter/blob/da08fa920f733f572a45329b25b78a712de47452/src/main/kotlin/com/modporter/core/transforms/structural/RegistrySourceBoundaries.kt) blob 8c7aa2ca95abc0f0dc3c78fc7084e5a52c764607。受け手の型で分岐: vanilla RegistryのgetRegistryKey()相当→key()、DeferredRegisterではgetRegistryKey()を維持。ParticleType<?> のregistry baseを保持し具象型を変えない。WritableRegistryでLifecycle.stable()→RegistrationInfo.BUILT_INはその型と条件が成立するときのみ。逆方向もreceiver・登録条件を再確認。テスト: ID・型・登録順序、イベント発火回数、欠落/重複。
## P03 — ItemStackの独自データ
Forge側（説明用断片、stack は ItemStack）:
```java
stack.getOrCreateTag().putInt("charge", 7);
```
NeoForge 1.21.1側（説明用断片、必要imports別途）:
```java
CompoundTag tag = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
tag.putInt("charge", 7);
stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
```
コピーの変更だけではstackへ反映されない。S1 [CopiedCustomDataWrites.kt](https://github.com/CrabMods/modporter/blob/da08fa920f733f572a45329b25b78a712de47452/src/main/kotlin/com/modporter/core/transforms/structural/CopiedCustomDataWrites.kt) blob 2283d9596b32ea8eb927adc02d90bebf6eb4d0d8: receiver型、alias、再代入、早期returnを確認する。S2 1.20.5 Primerはcomponentをimmutable扱い。vanilla固有の属性/ポーション等は専用componentを使う。逆は独自NBTに戻せる場合のみ、専用component・codec・default・remove semanticsは個別写像。テスト: 欠損値、更新、削除、save/reload、stack copy/split/merge、同期。既存world downgradeは別契約。
## P04 — Packet
Forge SimpleChannel + FriendlyByteBuf + NetworkEvent.Context → NeoForge CustomPacketPayload、TYPE、StreamCodec、RegisterPayloadHandlersEvent/PayloadRegistrar、IPayloadContext、PacketDistributor。登録方向・protocol、encode/decode、main/network thread、server authorityを維持。
S1 [PacketTablePayloads.kt](https://github.com/CrabMods/modporter/blob/da08fa920f733f572a45329b25b78a712de47452/src/main/kotlin/com/modporter/core/transforms/structural/PacketTablePayloads.kt) blob 7074e8734e3b2970e88e2b1a2c1b27ccc3c5f67e: abstract packet base + enum tableという限定構造を変換する。全通信方式の一般変換ではない。逆はpacket ID・direction・codec・threadingをSimpleChannelで明示、RegistryFriendlyByteBufの参照解決も再設計。テスト: roundtrip、無効payload拒否、server/client、再接続、wrong side。コード生成は対象の実APIを確認してから。
## P05 — CapabilityとAttachment
Capabilityは機能の公開・取得、Attachmentはデータ保有。全面置換ではない。NeoForge 1.21.1にはCapabilityもある。永続化するentity/chunk/block entityの状態はAttachment候補、itemはData Components、levelはSavedData候補。逆移植はForge Capability/独自NBT等へ意味を保って再実装。外部MOD API互換、invalidate、entity clone/death、syncは別検証。S2 attachments docs。テスト: lifecycle、保存、同期、外部consumer。
## P06 — 高リスク領域（規則未確定）
描画・Mixin/AT・worldgen・JSON/datagen・依存MOD・AI hookは型、descriptor、注入位置、registry/codec、resource pack/data pack版、client/server sideを個別確認。特に描画MOD間の互換性を名前だけで推定しない。既存ソースと版別Primerで調べ、未対応は明示。未解析領域を「自動で変換済み」にしない。
## 新規規則の追加
ID、方向と版、元/先コード、適用guard、反例・失敗修理史、保持する意味、検証、出典固定SHA/locator、状態を記録。既存IDの上書きより履歴付き追記。全規則の網羅・実行・独立検証は未実施。

# Spore 2.2.0j — 起動メタデータの原本検査

**2026-10-11 / ANCHOR = Minecraft 1.20.1 Forge / DIRECT_ARTIFACT。** ユーザー提供JARを解析。Forgeサーバー実起動、作者の修正前後の比較は NOT_RUN / NOT_VERIFIED。

## 原本照合と発見

- 対象: spore_1.20.1_2.2.0j.jar、116,439,461 bytes、SHA-256: d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。
- META-INF/mods.toml の実バイト SHA-256: 27672d03de388d129b19b49b01ec516454dac45e01c63c129c32499eb39b437e。Python tomllibによる構文読取PASS。
- 実際のMOD IDは **spore**。依存表の名前は **dependencies.examplemod** が2件。**dependencies.sporeは存在しない**。
- examplemod用のForge依存範囲は [47,)。Minecraft依存範囲は **[1.20,1.20.1)** で、上限が排他的なのでMinecraft 1.20.1を含まない。
- Forge公式 [1.20.x Mod Files仕様](https://docs.minecraftforge.net/en/1.20.x/gettingstarted/modfiles/) は、依存関係テーブル名を dependencies.(実際のMOD ID) と定義する。

**結論:** 元JARのSpore用依存関係の宣言が正しく紐付いていない。加えて、記載されたMinecraft版範囲も1.20.1を含まない。**Forgeが別MOD名に属するテーブルをロード時に無視するかエラー扱いするかはまだ実行していないので不明。** 実際の起動失敗や修正済みという主張はしない。

**原因候補（INFERENCE）:** Forge MDKのサンプル用 examplemod を置換し忘れた可能性。作者による説明・修復diffは未収集。正式なFAILURE-REPAIR-HISTORYの確定ケースではない。

## 実行した検査

- [自作の監査器](tools/audit_spore_metadata.py) はまず原本JARのSHAを固定照合し、TOMLの依存関係と区間を分析。
- [元JARの実測結果JSON](verification/mods_toml_audit_result.json) は2件の STATIC_FINDINGS を保持。
- 元JARで2回実行すると同一JSONバイト、異なるSRParasites JARでは BLOCKED_HASH_MISMATCHで終了コード2。原JAR、リソース、ソース全文は公共Gitに追加していない。
- [単体テスト](tests/test_gates.py) は合成TOMLでバージョン範囲の正誤を検証。

### 次の証拠

既存LABの権限と専用worldを固定し、原本のままForgeのDependency解析と起動ログを観測する。[GameTest契約](LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)に合致するまではランタイムNOT_RUN。別バージョンや改造JARを同一のSHAとして扱わない。

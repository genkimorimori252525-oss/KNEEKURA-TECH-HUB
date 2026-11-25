# Forge ≒ NeoForge 移植部
設立 2026-11-25 / Minecraft Technology Department
**目的：AIによる手動移植を速く、正確にする。自動変換エンジンを作らない。**
ForgeとNeoForgeの類似性を利用し、既存機能を保持したまま異なる環境へ移植する。ANCHOR は Forge 1.20.1、初期比較対象は NeoForge 1.21.1。両方向を別契約として扱う。他の版も需要に応じ追加する。Fabric変換は本部門の初期対象外。
## AIの入口
1. 元と先の Minecraft/loader/Java/mappings/依存MOD/ソースSHA、ライセンスを確定。元のビルド・機能・セーブ仕様を確認。
2. [SOURCES.md](SOURCES.md)から該当版の公式MDK・Primer・ModPorter規則を選ぶ。全資料の一括投入は禁止ではなく不要。既存プロジェクトの構成を維持できるなら維持。
3. [RECIPES.md](RECIPES.md)の索引から触るAPIのみ読む。loader差とMinecraft版差を分離。逆移植は前方ルールの単純反転禁止。
4. [PORT-TEMPLATE.md](PORT-TEMPLATE.md)で必要な差分、保存すべき意味、検証を記録。既存コードを最大限再利用。未対応箇所を黙って削除・スタブ化しない。
5. 別作業ツリーで小さな意味単位に変更し、コンパイルと対象機能の検証。実行は既存LABの権限・使い捨てworld契約に従う。
6. 再利用可能な規則・失敗・修正・検証版をこの部門へ戻す。製品コードは製品側。根拠不足の規則は CANDIDATE、ビルド済みと実行済みは分離。canonical VALIDATED は既存人間レビュー規則を守る。
## 三つの基盤
- ModPorter: 変換条件、拒否条件、回帰テスト、実MOD事例を研究する。実行・導入はしない。
- NeoForge Primers: Minecraft本体の版差、NeoForge差を別に調べる。
- NeoForge MDKs: 版別開発環境の原典。Forge向け legacy MDK も参照。既存ForgeGradleの一律変更はしない。
## 状態
初期資料・選定規則・AIテンプレートを設置。選定静的解析のみ、ローカルcheckout未確認、ビルド/実機/全規則収集 NOT_RUN。外部ツール、依存関係、常駐プロセス、CI、製品コード、既存LABに変更なし。公開リポジトリにつき原典リンクと派生記述のみ、元MOD/JAR/私的環境情報は保存しない。

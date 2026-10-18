# 限定サーバー検証：取得段階で停止

2026-10-18 UTC。限定した3ファイルの main 公開、ホスト型ランナーでの実験、原本コード／同梱アセット利用と Minecraft EULA の承認後に実施。

## 確認できた結果

- main 初回公開：`b4a2088c39a9fec55f365fd32c3536db9afc4573`。既存研究ブランチ全体のマージは行っていない。
- 初回 dispatch は YAML の job-level env で runner context が使えず 422。実ジョブなし。step env へ移す最小修正を `5d35329127427d7b43f12f0cf822fd5863ae64ab` で公開。
- [実ジョブ1](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/39144046129)：承認・コミット・ハッシュのチェック後、準備で失敗。原因を表示できず、固定の診断分類を追加。
- [実ジョブ2](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/39144331998)：`ACQUIRE_INSTALLER / HTTP_FAILURE`。HTTP ステータスを安全な整数として追加。
- [実ジョブ3](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/39144577957)：`ACQUIRE_INSTALLER / HTTP_FAILURE / 403`。main は `4866d7d7bbfe42a668437ebf38f8a13d6a3d59e7`。

3ジョブとも後片付け PASS、control BLOCKED、YSM NOT_RUN。実 Forge／YSM 起動、JNI 登録、ワーカー実行、描画を確認した結果ではない。403 の配布元側の詳細理由は不明。

## 修正と検証

修正はワークフローの context 配置と診断表示だけ。実行対象、通信制約、チェックサム、承認ゲート、コンテナ隔離を緩めていない。診断は固定 stage/error enum、HTTP 状態整数、固定 Docker コマンド種別と終了コードのみ。任意のログ・例外本文・ヘッダー・URL は出力しない。

最新の自作偽入力テスト21件を実装側・独立レビュー・統合側で確認。これは実インストーラーやゲームの統合成功を意味しない。初期 `review-receipt.json` と `INDEPENDENT-REVIEW.md` は初期17件時点の履歴であり、最新ファイルのハッシュは [execution-receipt-2026-10-18.json](execution-receipt-2026-10-18.json) を使う。

## 再開条件

公式インストーラー取得に対するアクセス拒否が解決したことを確認してから、同じ限定実験の再開を判断する。403 回避のための User-Agent 偽装、別経路への切替、通信・認証・隔離設定の緩和、自宅PCへの実行移転はしていない。自動再試行や継続監視は設定していない。

main の最新コミット、公開状態、既存ワークフローと3ファイルだけの差分、ロック／ハーネスのハッシュを再確認する。過去の dispatch 入力の expected_commit をそのまま流用しない。成功してもクライアント描画や全 native 動作の確認へ拡大しない。

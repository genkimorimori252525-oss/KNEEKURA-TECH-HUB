# Fungal Infection: Spore 2.2.0j — Failure/Repair History（限定的な開始記録）

**2026-10-11 / ANCHOR Minecraft 1.20.1 Forge / 履歴coverage PARTIAL / 公式修復と再現は未検証。**

正式な機械可読記録：[FAILURE-REPAIR-HISTORY.json](FAILURE-REPAIR-HISTORY.json) はTECH-HUB既存形式 kneekura.failure-history.v1 で作成した。現在は **case数0**。これは問題が存在しないという意味でも、原作者が修正したという意味でもない。現時点ではCASに固定された証拠document_id/index_snapshot_idを取得しておらず、**形式上の候補caseへ虚偽のEvidence IDを登録しない**ため。

## 選択した小さな履歴ウィンドウ

- **Spore:** ユーザー提供 spore_1.20.1_2.2.0j.jar / SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489 / All Rights Reserved。
- **報告:** [DynamicTrees Issue #1201](https://github.com/DynamicTreesTeam/DynamicTrees/issues/1201)、2026-07-09、1.20.1 Forge 47.4.20 / Dynamic Trees 1.20.1-1.4.11 / Spore 1.20.1_2.2.0j。調査時 IssueはOPEN、修正PRとの確定リンクなし。Issue内容は第三者報告。
- **比較ソース:** DynamicTrees [release/1.20.1 @ eb7f75e9](https://github.com/DynamicTreesTeam/DynamicTrees/tree/eb7f75e9f0f021503349893cf6ecb8ee864a3053)、gradle.propertiesでmodVersion=1.4.11を確認。TrunkShellBlock.javaのgetHardness/getMuse/getMuseDirの原典を閲覧した。
- **対象機構:** Gargoyl.SmashStompのBlockState/BlockPosミスマッチ → Dynamic Trees coredir参照の失敗という具体的な仮説。

[詳細な静的照合と原典の場所](GARGOYL-DYNAMICTREES-HARDNESS-2026-10-11.md) / [4件の元Bytecode契約の結果](verification/GARGOYL-HARDNESS-STATIC-2026-10-11.json)。この発見はREPORT＋DIRECT_BINARY＋DIRECT_SOURCE＋INFERENCEを分ける。実ゲーム内で再現した原因や公式修復ではない。

## なぜまだ正式なRepair Caseでないか

TECH-HUBの[Failure/Repair規約](../../FAILURE-REPAIR-HISTORY-v1.md)では、原文/Issue/修正diffを既存のCASへ取得し、snapshot/document IDを発行する必要がある。本調査では既存の外部GitHubツールで閲覧しただけで、当該原文をCASへ固定していない。修復前後のSpore作者によるコミット/配布JAR差も確認できない。よってcas.importとVALIDATEDの昇格は**NOT_RUN**、coverageは**PARTIAL**、正式caseは空のままにしている。

## 次に取得する証拠

1. Issue #1201 の本文とコメント、Dynamic Trees 1.4.11ソース、固定Spore JARクラスBytecodeを、各原本種別・SHA・CAS id付きで選定snapshotへ取り込む（必要に応じ権利・ファイル制限を守る）。
2. Gargoyl発生時の候補座標・中心座標・BlockStateを計測する専用の**隔離Forge world**を用意し、Spore/Dynamic Trees以外のMODを可能な限り除いた再現条件を比較する。
3. もし後続のSpore/Dynamic Trees修正が存在すれば、修正前/修正後のコミットまたはartifact差分、回帰テストまで取得する。Issueクローズのみでは固定成功としない。
4. 元JARや生ログをpublic Gitに保存しない。症状再現なしでも、呼出側の「BlockStateと問い合わせ座標を一致させる」という移植時の設計候補は別に維持する。

**結論:** 引き続き PARTIAL / BUG_CANDIDATE。最新NeoForgeなど別トラックの改善を、このForge1.20.1対象の正式修復成果に転用しない。

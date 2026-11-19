# TLM integration reference archive

ここは、TLM本体から分離した後も関連テストを再現できるように残す
**参考アーカイブ**です。ここにあるコードはLABのbridgeへ自動登録されず、
TLM本体へコピーして使う場合にだけ有効です。

## `/tlm sim`

`SimCommand.java` は旧 `/tlm sim itemttl` / `/tlm sim status` の実装です。
利用する場合はTLM側の `RootCommand.register` で次を登録します。

```java
root.then(SimCommand.get());
```

このコマンドは `SimArena.itemTtlTicks` を変更するため、TLM側の
`com.github...sim` 実装と同じクラスパスで動かす必要があります。

## 実行配線

旧 `runSim`、`prepareSimRun`、`schemaTraceTest` のGradle設定は、現在のTLM本体の
Gradleへ戻さず、必要なテスト環境で個別に復元してください。スキーマ検査は
リポジトリルートの `npm test` / `node simlab/schema-check.mjs` が正規経路です。

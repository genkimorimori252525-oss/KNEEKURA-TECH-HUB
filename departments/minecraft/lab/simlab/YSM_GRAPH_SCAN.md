# YSM runtime graph walk

`SimYsmObjectWalker` は難読化された YSM runtime object graph を、**未知メソッドを呼ばず**
field と JDK container だけで探索する共通基盤。

`SimYsmGraphScan` はその walker 上で cube/bone 数に対する container shape だけを分類する。
Molang state などの意味づけは行わない。

## Why container traversal matters

YSM内部objectが直接fieldとしてぶら下がるとは限らない。

~~~text
geo model
  -> List
     -> Map
        -> object[]
           -> evaluator/state object
~~~

旧walkerは array / Map / Collection を候補として記録した時点で葉扱いしていたため、
container内部のobjectへ到達できなかった。

共通walkerは:

- ordinary object field
- object array element
- Map key/value
- Collection element

を同じidentity graphとして辿る。

primitive arrayは値グラフとしては葉のまま。GraphScanでは候補shapeとしては記録する。

## Safety

未知YSM objectでは `Field#get` 以外のmethodを呼ばない。

JDKの Map / Collection iterationだけはインターフェース契約上のcontainer走査として使用する。
循環は identity set で止める。

## Shared budgets

`SimYsmObjectWalker` が以下の唯一の定義元になる。

- max depth: 6
- max visited graph nodes: 40000
- max traversed elements per container: 64

GraphScanとscalar/state probeは同じbudget/completeness契約を共有する。

候補shapeのsize自体は元のfull sizeを記録する。
64要素を超えるcontainerは、shapeは失わず、子object traversalだけを64件で止める。

## Completeness

`Report` は:

- `truncatedContainers`
- `depthBudgetExhausted`
- `visitBudgetExhausted`
- `complete()`
- `negative`
- `conclusiveNegative()`

を持つ。

~~~text
negative=true, complete=true
=> この探索範囲では候補不在を確定できる

negative=true, complete=false
=> 候補はまだ見つかっていないが、未探索が残る
~~~

「未探索」を「存在しない」に変換しないことが最重要。

## Next use: Molang evaluator/state search

M5までのnetwork evidenceで:

~~~text
packet receive
 -> Reimu handler
 -> sendCommand
 -> Forge client command consumed
~~~

までは観測できる。

次に知りたいのは YSM内部でMolang expressionが評価され、runtime variable/stateへ反映された境界。
`SimYsmScalarProbe` は同じwalker上でfield scalarと `Map<String, scalar>` をsnapshotし、
controlled mutationのbefore/after差分を取る。

候補を見つけても、名前や意味を即断しない。
詳細は `YSM_MOLANG_STATE_PROBE.md` を参照。

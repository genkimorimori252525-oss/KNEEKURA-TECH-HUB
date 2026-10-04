# 軽量化 MOD target template

target path:

`departments/minecraft/optimization/mods/<slug>/`

## README minimum

```text
# <Target>

Status:

## ANCHOR
Minecraft:
Loader:
MOD version:
Artifact:
Source:
Revision:
License:

## FRONTIER
Minecraft:
Loader:
MOD version:
Source:
Revision:

## Optimization categories
- ...

## Main mechanisms
- ...

## Correctness boundary
- ...

## Benchmark state
NOT_RUN / LOCAL_EXPLORATORY / LOCAL_REPEATED / REPRODUCED_SECOND_ENV

## Compatibility
- ...
```

## Finding template

```text
Finding:
Category:
Track:
Evidence basis:
Performance state:

Baseline behavior:
Optimization target:
Mechanism:
Eligibility guard:
Fast path:
Fallback:
Cache/invalidation:
Allocation effect:
Concurrency owner:

Correctness invariant:
Known regression:
Compatibility surface:

Benchmark workload:
Metric:
Result:
Uncertainty:

Source locator:
History locator:
```

## Suggested files

- `README.md`
- `SOURCE-INVENTORY.json`
- `ARCHITECTURE.md`
- `OPTIMIZATIONS.md`
- `CORRECTNESS.md`
- `BENCHMARKS.md`
- `COMPATIBILITY.md`
- `FAILURE-REPAIR-HISTORY.md`
- `VERSION-PORTABILITY.md`
- `LICENSE-PROVENANCE.md`

## Do not do

- source diffだけで実測性能を断定しない
- author benchmarkを自分の再現結果にしない
- FPSだけでserver optimizationを評価しない
- performance gainとsemantic changeを混ぜない
- targetを通常mods/とoptimization/mods/へ重複コピーしない

# 軽量化 Benchmark Specification v1

## 1. Principle

ベンチマークは「MODの勝敗表」ではなく、**どの技術がどのworkloadで効くか**を測る。

原則は paired A/B。

```text
A = baseline
B = optimization enabled

same:
Minecraft
loader
modpack
world/seed
config
JVM
hardware
driver
resolution
view distance
scenario
measurement window
```

## 2. Warm-up and measurement

- startup系を除き、JIT/asset/chunk/cache warm-upとmeasurementを分ける
- cold-cache と warm-cache は別scenarioにする
- GC直後など都合の良い瞬間だけ切り取らない
- 少なくとも複数runを保持する
- outlier除外をした場合は規則を先に固定する

## 3. Main metrics

### Client rendering
- FPS は補助
- frame time median
- frame time p95
- frame time p99
- stutter count / long-frame count
- CPU render-thread time
- GPU time
- VRAM

### Server/simulation
- MSPT median
- MSPT p95 / p99
- TPS saturation
- tick phase cost
- entity/block entity count
- main-thread utilization

### Memory
- heap used
- retained heap if available
- RSS
- allocation bytes/sec
- allocation count
- young/full GC count
- GC pause duration

### Startup/load
- JVM start → title
- world load time
- datapack reload
- resource reload
- model bake
- mod discovery/classloading

### Chunk/world
- chunks generated/sec
- chunks loaded/sec
- save throughput
- region IO bytes
- task queue latency

### Network
- bytes/sec
- packets/sec
- duplicate/state-delta reduction
- server/client processing time

## 4. Workload identity

ベンチ結果は workload ID を持つ。

例:

```text
CLIENT_STATIC_BASE
CLIENT_FAST_CAMERA
CLIENT_ENTITY_DENSE
SERVER_VILLAGER_DENSE
SERVER_BLOCKENTITY_DENSE
CHUNKGEN_FLYOVER
WORLD_LOAD_COLD
WORLD_LOAD_WARM
RESOURCE_RELOAD
```

target固有scenarioを追加してよい。

## 5. Reproducibility record

最低限:

```text
Minecraft:
Loader:
Target MOD:
Baseline mods:
World/seed:
Dimension:
Position/route:
Entity counts:
View/simulation distance:
Resolution:
Shader:
JVM:
Heap:
Java:
CPU:
GPU:
RAM:
OS:
Driver:
Run count:
Warm-up:
Measurement duration:
```

## 6. Correctness sidecar

各benchmark runに性能以外のacceptanceを持たせる。

例:

- expected chunks visible
- no missing meshes
- same entity count
- same world hash where applicable
- same lighting checksum/sample
- no errors/exceptions
- no stuck async tasks
- save reload succeeds

性能が良くてもcorrectness acceptanceが落ちたrunは単純PASSにしない。

## 7. Reporting

推奨:

- raw run values
- median
- p95/p99 where meaningful
- delta absolute
- delta percent
- confidence/noise note

単一平均だけにしない。

## 8. Hardware scope

一台の結果はそのhardware classの結果。

CPU-bound / GPU-bound / memory-bound が変われば効果も変わる。

必要なら:

- low-end CPU
- high-end CPU
- integrated GPU
- discrete GPU
- low-memory heap

を別profileにする。

## 9. Benchmark status

- `NOT_RUN`
- `LOCAL_EXPLORATORY`
- `LOCAL_REPEATED`
- `REPRODUCED_SECOND_ENV`
- `INCONCLUSIVE`
- `REGRESSION`

## 10. Do not claim

- author benchmarkだけで自分のruntime結果扱い
- FPS screenshot一枚から普遍性能
- modpackが違うA/B比較
- warm/cold混在比較
- correctness failureを無視した高速化

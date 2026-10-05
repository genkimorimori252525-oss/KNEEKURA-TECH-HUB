# Yes Steve Model failure / repair history

Research date: 2026-10-05

This file records failures as engineering evidence. A community issue is never treated as a repaired
fact unless a source/history/runtime link establishes the repair.

## 1. Why YSM history is unusually useful

The official public repository now contains historical commits from the 2.6.x line as well as the
new 3.0-dev reconstruction.

That makes it possible to learn not only what the code looks like, but which boundaries repeatedly
failed:

- render-context identity;
- first-person / shadow context;
- model-reset ownership;
- optional-mod compatibility;
- model-load failure handling;
- Molang event lifecycle;
- TLM transforms;
- opaque/translucent rendering;
- async animation context.

These are exactly the kinds of failure/repair pairs KNEEKURA wants to preserve.

## 2. 2025-12-03 — Iris shadow render context

### Failure

Commit predecessor behavior treated render immutability too broadly for the local player during Iris
shadow rendering.

### Repair

Official commit:

- 32b041defdafce891caf141858bd75374adcb12c
- message: 修复 iris 阴影渲染时动画更新潜在的问题

The repair distinguishes generic scene/shadow immutability from the local-player exception and adds
Iris awareness to the player entity path.

### Reusable lesson

**Render pass is part of state identity.**

A pose that is safe to reuse for a world entity is not automatically safe for:

- local first-person;
- shadow pass;
- paper doll;
- inventory;
- third-party camera/render pass.

Do not cache only by entity + frame.

## 3. 2025-12-22 — async animation and Better Combat first-person interaction

### Failure

Async update context and first-person compatibility were coupled badly enough to produce disabled
updates / incorrect first-person rendering.

### Repair

Official commit:

- 2b59dacafd533dc17df371407580e8cd4e0737a2
- message includes:
  - split animation update context;
  - fix async animation update failure;
  - fix Better Combat first-person rendering issue.

The diff moves Better Combat handling from mutating a head bone inside animation code toward a
renderer-level skip decision.

### Reusable lesson

**Compatibility decisions that determine whether a representation should render belong near the
render/integration boundary, not as hidden bone mutations inside the generic animation core.**

## 4. 2026-01-15 — client model-load failure path

### Failure

A failed/absent client model build could enter a bad synchronization lifecycle.

### Repair

Official commit:

- 99e4c493520666f1f9b579574ad4626c60f12ac0
- message: 处理客户端模型加载失败的情况

ClientModelManager was changed to accept a nullable model-data result and to avoid running the normal
model-build/registration path when model data is absent.

The later 2.6.3 release notes also describe a model-sync hang caused by client-side model build
failure, reinforcing this as a real lifecycle boundary.

### Reusable lesson

**Asset transfer completion and asset activation success are different states.**

A failed decode/build must produce a terminal failure that retires the request/session; it must not
leave the peer waiting for a Ready state that can never occur.

## 5. 2026-03-31 — Molang events lost during reset/model lifecycle

### Failure

Some Molang events stopped firing.

### Repair

Official commit:

- 4a2c97a447de43edab122895bec2f3e09d02dcf4
- message: 修复部分 molang 事件失效的问题

The diff reorganizes reset responsibilities:

- model-container-level state such as defer/sync handlers is reset with the model container;
- geometry-level reset handles geometry/animation state;
- player/projectile/vehicle reset ordering is corrected.

### Reusable lesson

**Reset scope must match ownership scope.**

Do not put all cleanup into one generic reset function.

Use separate lifecycle owners for:

- asset/container identity;
- geometry/pose state;
- controller/event handlers;
- entity-specific presentation state;
- integration state.

Otherwise a geometry reload can accidentally destroy event wiring that should live until a model
container changes.

## 6. 2026-04-11 — compatibility version drift and high-risk integrations

### Failure class

Optional mods changed internal/core APIs often enough that YSM integration could crash rather than
degrade gracefully.

### Repairs in the 2.6.5 line

Official history includes:

- b7ec499c2096de961c033a6943651d0c5bb7f818 — improved mod compatibility detection;
- 71625e2949cb40c4bf663776c7cb1f878ebd994e — configuration to disable Sophisticated Backpacks compatibility;
- the 2.6.5 distribution changelog states linked features are automatically disabled when the linked
  mod version is too old and adds disable switches for high-risk integrations.

### Reusable lesson

A compatibility adapter needs its own **capability gate**:

~~~text
mod present
   |
version/API compatible?
   | yes
adapter enabled?
   | yes
register integration
~~~

Presence alone is not sufficient.

## 7. 2026-04-11 — UI work from the wrong thread

### Failure

Radial configuration controls could be added from a non-main thread.

### Repair

Official commit:

- 75d5a46dccf45b7705aa62792e9a8e6a178e70c0
- message: 修复轮盘配置控件添加不在主线程上的问题

### Reusable lesson

Async model/animation work must never blur the ownership of Minecraft/UI objects.
Worker threads should publish immutable results; UI/game objects are updated by their owner thread.

## 8. 2026-04-17 — opaque rendering and model memory

### Repair/optimization

Official commit:

- 6824eae72c78bb444d579a86b1d617905a37c3d4
- message: 优化不透明模型的渲染；改进模型内存管理

The official 2.6.5 changelog presents the same optimization theme and warns that using
semi-transparent textures significantly reduces rendering efficiency.

### Reusable lesson

Do not put opaque and translucent geometry through the same cost model.

For KNEEKURA:

- fast opaque path;
- explicit translucent path;
- measure sorting/overdraw separately;
- surface transparency as a model-budget choice, not a free visual feature.

## 9. 2026-04-18 — 2.6.5 source line establishment

History:

- e1413f7 — version 2.6.4 -> 2.6.5
- fb23351 — bundled model fixes while declaring 2.6.5
- f184eda — Fast DEV build task while declaring 2.6.5

This sequence is why f184eda is treated as a **release-line source candidate**, not as a proven
binary-source identity.

## 10. 2026-09-20 — FRONTIER RenderContext cache bug

### Failure

The 3.0-dev path could reuse an already-extracted frame while leaving old RenderContext metadata in
the reusable render-data object.

Async scheduling also checked a model-presence condition that was not the same as having a renderable
model loaded.

### Repair

Official commit:

- d6f0eb71ae2943918f85a1608d21452ba51917b5
- message: 修复 RenderContext 异常缓存问题

The diff:

- refreshes renderData.ctx even when immutable pose extraction is reused;
- adds hasRenderableModel and uses it for async scheduling.

### Reusable lesson

**Pose cacheability does not imply metadata cacheability.**

Split:

- reusable pose/extracted geometry state;
- draw/pass-specific context metadata.

## 11. FRONTIER self-documented unresolved risks

Current official known-issues are themselves failure evidence.

### Animation

- isMoving logic error.
- async evaluation reads live mutable game state without an immutable snapshot.
- controller/Molang once-only behavior lacks real Forge end-to-end proof.
- same-frame context metadata may leak across passes.
- in-place pose/snapshot mutation has no transactional rollback.
- Molang performance/complexity limits are not established.
- model hot-swap lifecycle is not fully closed.
- cross-language bone layout lacks independent golden verification.

### Rendering

- native render failure has no alternate output/fallback.
- shared renderer scratch is non-reentrant and requires global serialization.
- task scheduling is based on CubeGroup count rather than measured cost.
- transparent sorting is local, not globally solved.
- several attachment/first-person paths are not fully connected.
- no complete automated visual-regression closure.

### KNEEKURA response

These should become design requirements, not TODOs discovered after implementation:

1. immutable sampled animation input;
2. staged pose update + commit;
3. generation token on deferred work;
4. separate pose and draw metadata;
5. golden cross-language layout tests;
6. renderer failure fallback;
7. measurable work units for scheduling;
8. explicit transparent budget;
9. end-to-end multiplayer/session tests;
10. visual golden tests for each render context.

## 12. Open community issue: 2.6.5 dedicated-server model sync stall

### Community evidence only

Official issue tracker #444, opened 2026-10-03, reports:

- YSM 2.6.5 / Forge 1.20.1;
- session/index appears to arrive;
- client model-content directory remains empty;
- server model cache is populated;
- the same pack had previously completed two sync sessions;
- many configuration/environment variables were tested without resolving it.

The reporter asks whether the transfer is blocked between index publication and content transfer and
whether Molang readiness can affect the Ready state.

### Status

**OPEN / NOT ROOT-CAUSED / NOT PROMOTED TO IMPLEMENTATION FACT**

### Why it matters

The symptom aligns with a general lifecycle hazard already visible in YSM history:

~~~text
catalog/index known
      !=
content transferred
      !=
content decoded
      !=
render target ready
~~~

The FRONTIER explicitly separates catalog publication and content activation, which is a stronger
model for reasoning about this class of failure.

## 13. Failure patterns to preserve in KNEEKURA knowledge

| Pattern | YSM evidence | KNEEKURA rule |
|---|---|---|
| Render pass changes semantics | Iris / RenderContext fixes | render context is part of cache key/metadata |
| Asset received but not usable | model-load failure + issue #444 hint | transfer and activation are separate terminal states |
| Generic reset destroys specialized state | Molang event reset fix | cleanup follows ownership layers |
| Optional mod present but incompatible | 2.6.5 compatibility changes | gate adapter by API/version/capability |
| Async work touches owner-thread objects | radial UI fix | publish data, mutate owner objects on owner thread |
| Transparency destroys fast path | 2.6.5 render optimization | separate opaque/translucent budgets |
| Shared pose reused with stale draw metadata | 3.0 RenderContext fix | pose cache != pass metadata cache |
| Live mutable input read off-thread | 3.0 known issue | snapshot before worker evaluation |
| Cross-language layouts can drift | 3.0 known issue | golden ABI/layout tests |

## 14. Status

Failure/repair history: **EVIDENCE_BACKED_BOUNDED**

Still needed:

- link more official issues to the exact repair commits;
- runtime reproduction of selected 2.6.5 failure classes;
- performance regression measurements;
- long-soak memory/model-swap verification.


## 15. 2026-10-05 — first exact-JAR scanner run did not execute

### Failure

The first exact-artifact CI pass successfully:

- fetched the official Modrinth JAR;
- computed the correct SHA-256 / SHA-1;
- verified the exact binary size.

But the Python structural scanner produced no `structure.json`.

Cause:

- `main()` was defined;
- the initial committed script omitted the module entrypoint that calls it.

The following reporting step therefore failed because its expected result file did not exist.

### Repair

- add `if __name__ == "__main__": main()`;
- rerun against the same exact Modrinth artifact;
- verify the exact same artifact hash;
- keep the failed CI run in history.

The corrected scanner subsequently parsed all **955** classes with zero parse errors.

### Reusable lesson

An evidence tool must verify **its own output contract**, not merely that prerequisite acquisition
succeeded.

For future KNEEKURA evidence pipelines:

~~~text
acquire target
 -> verify identity
 -> run analyzer
 -> assert expected result file/schema exists
 -> validate result invariants
 -> publish minimized evidence
~~~

Do not collapse “artifact acquisition succeeded” into “analysis succeeded”.


## Bounded seed continuation — tool limitations

The local `javap` command was unavailable. Five Java declaration shapes and 16 selected method reference
paths were instead read by the retained bounded classfile audit tool. The scratch-only documentation
refresh helper initially had a syntax error; it was repaired before any refresh output was accepted.
The final exact artifact contract and seed audit both have 0 failures. These checks do not claim runtime
execution or native correctness; integer accessor ambiguities and source/artifact divergence remain.


## Molang evaluation continuation — existing-owner audit regression

The first new dossier audit raised KeyError for ArgumentCollection: the bounded inventory included
only newly seeded class owners, while two new member mappings belonged to a previously mapped owner.
The repair inventories the union of class, member and bounded-support owners. The two accessor rows
remain the normal regression case in the durable dossier. Fresh old/new audits pass 66/106 checks
with zero failures. Relation, branch target, catch type and code digest mutations each exit1.

The first delegated reconnaissance model was unavailable; authorized Sol reconnaissance completed
the bounded primary-source work. Chinese wiki direct reads timed out; indexed snippets remain leads
only. An additional broad search returned irrelevant results. No runtime or native result is inferred
from successful structural verification. The earlier integer accessor ambiguity is resolved only by
the new independently evidenced converter calls, leaving the historical negative record intact.


## Concrete evaluator evidence — predicate wording repair

Independent review found the comparison helper used unordered reference-presence conjunctions,
while its labels said reference paths. The durable dossier now names reference_presence_count and
coarse_reference_presence_accepted and states this distinction. The durable audit independently
checks complete ordered reference paths and full selected instructions/handlers; no mapping was
changed by this wording repair. Its opt-in detailed operand schema captures signed switch targets
and numeric constants while leaving old dossiers unchanged. Fresh92/106/66 audits have0failures;
six intended lifecycle/control-flow mutations each fail. No runtime failure or protected-native
behavior was inferred. Existing javap limitation is unchanged.

## Practical campaign repair record — 2026-10-05

- The integration guard caught server/client MolangCommand simple-name ID collision before map
  write; one ID was package-qualified. Exact targets remain distinct; all 604 IDs/targets are unique.
- Baseline total 848 unseeded was correct; 618 main + 214 media + 15 UNKNOWN omitted one RENDERER
  singleton. There have always been 16 singleton components. AnimationUtils is now mapped; final
  432 main + 214 media + 15 isolated = 661 unseeded. Graph topology is unchanged.
- Final index review caught raw cluster keys replacing consumer `mapped/score/priority` keys.
  Restored the original top-level index format/date/keys/15-entry unknown inventory, plus the 11-column compact class schema and short class identifier values for all 955 rows, with regenerated values and
  294 mapped classes. Preserved historical document hashes while refreshing only current blocks.
- Durable audit now checks encoded operands, ConstantValue, constructor-registration paths and
  BootstrapMethods connections; ten meaningful corrupt-evidence controls reject.
- Corrected duplicated RealCamera method counts, maid vehicle labels, Molang packet dispatch,
  pi/e Float storage, partial finally coverage and Token tag wording. No confidence promotion
  conceals source/SRG/runtime uncertainty. Whole copied Java source bodies were removed from new
  dossiers; hashes, URLs, bounded prose and exact artifact support remain.
- All 18 concrete source leads previously hidden by propagated MOLANG labels received actual
  comparison and class-only HIGH roles. One independently sourced singleton also closed. Prior
  585 and original 282 rows remain identical; no generic source-candidate deferral remains.

- Final full-schema review also caught raw foundation format/header replacing the index format,
  dropping recorded_at and the compact unknown inventory. Restored the complete original top-level
  contract, .index.v1 format/date, short identifiers and unchanged 15-entry unknown metadata.
  This correction precedes remote publication; graph and semantic role counts are unchanged.

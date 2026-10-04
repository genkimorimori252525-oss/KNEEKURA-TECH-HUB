# Yes Steve Model architecture research — 2026-10-05

## 1. Research question

What parts of YSM are reusable as general character/model technology for KNEEKURA, especially for
non-player entities, Touhou Little Maid integration, animation control and future custom mobs?

Evidence labels:

- **DIRECT_SOURCE** — directly visible in an official pinned source revision.
- **HISTORY** — supported by an official commit/diff.
- **OFFICIAL_DOC** — stated by the official current architecture/status documentation.
- **DISTRIBUTION** — official release metadata/changelog.
- **COMMUNITY_HINT** — issue/Reddit/community report used only to choose what to inspect.
- **INFERENCE** — KNEEKURA engineering interpretation.
- **UNKNOWN** — not established.

Track rules:

- ANCHOR candidate: official source revision f184edabd1b5115ce5a24cb6d155ba5a669f5ba6, declaring 2.6.5-forge+mc1.20.1.
- FRONTIER: official dev/1.20 revision 74c53b58b2f9b680a6c6dc5d5d41e7422fc000bb, declaring 3.0-dev-forge+mc1.20.1.
- Never attribute FRONTIER-only structures to the distributed 2.6.5 binary.

## 2. 2.6.5 is already a semantic animation runtime, not just a renderer

**DIRECT_SOURCE**

Anchor AnimatableEntity owns, per wrapped Minecraft entity:

- AnimationData
- AnimationProcessor
- RateLimiter
- EntityStateTracker
- PhysicsManager
- current GeoModelState
- event handlers
- coded-controller states
- frame/update bookkeeping

Locator:

- src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/AnimatableEntity.java

This matters because the mutable animation state belongs to the **entity instance**, not to a shared
model asset.

**INFERENCE**

That is the correct direction for KNEEKURA NPCs. One geometry/model asset can be shared, while
Reimu, a maid, a player and another mob keep independent animation/controller state.

## 3. Entity state is sampled into a render/animation event

**DIRECT_SOURCE**

Anchor AnimatableEntity.updateAnimation gathers Minecraft-side state such as:

- passenger/sitting status
- walk animation speed and position
- child state
- body/head interpolation
- head pitch and net head yaw
- tick/partial-tick time

It then builds EntityModelData, a MolangContext and an AnimationEvent before advancing the animation
runtime.

This is a useful boundary:

~~~text
live Minecraft Entity
      |
      v
sample / normalize
      |
      v
animation input context
      |
      v
controllers + Molang
~~~

**INFERENCE**

Do not let every animation expression query arbitrary game objects directly. A normalized animation
input layer is easier to test, replay and eventually move off-thread.

The current FRONTIER documentation independently identifies the danger of asynchronous evaluation
reading live Entity/level/Minecraft inputs without an immutable snapshot. That confirms the design
pressure: the sampling boundary should become explicit and immutable before parallel evaluation.

## 4. Visibility and distance control animation work

**DIRECT_SOURCE**

Anchor AnimatableEntity.getFrameRateLimit changes the animation rate limit for non-local entities:

- if the entity was not rendered in the previous frame: 10
- if distance is greater than 64 blocks: 30
- if distance is greater than 40 blocks: 60
- otherwise: current refresh rate

The exact numbers are YSM-specific and must not be copied blindly.

**INFERENCE**

The reusable technique is **per-entity animation quality-of-service**:

~~~text
visible + near        -> high animation update budget
visible + far         -> reduced budget
culled / not rendered -> strongly reduced budget
~~~

This is more useful than a single global animation tick rate for a village or battle scene with many
animated NPCs.

## 5. Animation update and visual render are intentionally not identical operations

**DIRECT_SOURCE**

Anchor tickAnimation distinguishes:

- whether a frame should advance logical animation state;
- whether a render context still requires a visual update;
- whether state tracking should tick;
- whether code animation should be reapplied.

It also refuses to move animation time backward, with a source comment noting possible replay impact.

**INFERENCE**

KNEEKURA should distinguish at least:

1. sampled game state;
2. logical animation/controller advance;
3. pose extraction;
4. render-pass-specific mutation;
5. final draw.

Treating all five as one render callback creates replay, shadow, paper-doll and first-person bugs.

## 6. Molang execution is queued around animation evaluation

**DIRECT_SOURCE**

Anchor AnimationProcessor contains a ConcurrentLinkedQueue of MolangExecutionTask.

AnimatableEntity.executeMolangExp does not immediately mutate controller state. It enqueues an
expression with:

- expression value
- allow-emitting flag
- pre/post phase flag
- optional result callback

AnimationProcessor drains tasks around the controller/animation evaluation path.

Locator:

- src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/processor/AnimationProcessor.java

**INFERENCE**

This is a useful command-buffer pattern: external integration code can request an animation-side
operation without executing arbitrary Molang immediately at the call site.

However the FRONTIER known-issues document explicitly says once-only behavior and queue-drain timing
are not yet end-to-end proven in a real Forge world. KNEEKURA should preserve the queue idea but give
it a stronger contract:

- exact producer thread;
- exact consume phase;
- at-most-once execution;
- model generation/revision attached to the task;
- deterministic discard rule on model swap.

## 7. Controller polymorphism is a major reusable part

**DIRECT_SOURCE**

The anchor contains:

- CodedAnimationController
- BedrockAnimationController
- HybridAnimationController
- IAnimationController

BedrockAnimationController supports multiple active animation players and per-bone blend queues.

It also supports nested subcontrollers with a hard maximum hierarchy depth of **5**.

Locator:

- src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/controller/BedrockAnimationController.java

The 2.6.3 release history also introduced Bedrock-controller calls into hard-coded controller logic
and the subcontroller system.

**INFERENCE**

The important technique is not the number five. It is a common controller interface that lets a
character combine:

- code-owned locomotion/combat decisions;
- data-driven Bedrock state machines;
- hybrid overrides.

That is directly useful for a KNEEKURA character whose base locomotion is generic but whose
character-specific attacks and expressions are model data.

## 8. Bone semantics are flattened before the hot render boundary

**DIRECT_SOURCE**

Anchor GeoModelState creates arrays sized from the sorted bone list:

- input-state stride: 12 floats per bone
- output-state stride: 4 floats per bone

It builds a name-to-bone-state map and also resolves semantic groups/locators including:

- head
- left/right hand
- additional hand groups
- passenger groups
- elytra
- pistol/rifle
- waist/shoulder
- blade/sheath
- backpack
- first-person head
- first-person view locator

Locator:

- src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/GeoModelState.java

The class also contains a direct TLM conversion cache with a FIXME saying the coupling should not
really exist.

**INFERENCE**

Two reusable ideas are separate:

### A. Flat hot-path state

Keep expensive semantic objects out of the innermost renderer. Resolve them to compact indexed
state once.

### B. Semantic locators

Equipment and attachments should bind to named semantic locators rather than hard-coded model
coordinates.

The TLM FIXME also gives a negative lesson: conversion/adaptation caches should live in an adapter
layer, not in the generic core model-state object.

## 9. 2.6.5 Java/native boundary

**DIRECT_SOURCE**

Anchor NativeRenderer.renderModel receives:

- VertexConsumer
- PoseStack pose
- GeoModel
- input-state float array
- optional output-state float array
- texture index
- render mode
- light/overlay/color/alpha
- GUI/context information

It then calls native nRenderModel.

A Java LegacyWriter fallback bridge receives flattened vertex arrays with position, color, UV,
normal, overlay and light fields and writes them through VertexConsumer.

Locator:

- src/main/java/com/elfmcys/yesstevemodel/geckolib3/geo/NativeRenderer.java

**EVIDENCE BOUNDARY**

This proves the Java/JNI **contract** of the release-line source candidate.
It does not prove the internal implementation of the distributed protected native library.

**INFERENCE**

The clean reusable principle is:

> Keep animation semantics and ownership in the game-language layer; accelerate geometry math behind
> a narrow data-oriented boundary.

That gives KNEEKURA freedom to replace the accelerated backend later without rewriting controller
semantics.

## 10. Parallel animation uses a schedule / join barrier

**DIRECT_SOURCE**

Anchor AnimationParallelTicker maintains weak references to animatable wrappers.

scheduleAll:

- removes dead/inactive wrappers;
- refreshes model state;
- skips entities whose async update is disabled/not initialized/not present;
- obeys client disable categories;
- calls beginAsyncUpdate;
- adds the entity to a task list.

waitAll waits for every scheduled entity and then clears the task list.

Locator:

- src/main/java/com/elfmcys/yesstevemodel/client/animation/AnimationParallelTicker.java

**INFERENCE**

The reusable pattern is a bounded frame phase:

~~~text
main thread sample/schedule
          |
          v
parallel animation work
          |
          v
explicit join barrier
          |
          v
render commit
~~~

The FRONTIER known-issues notes that live game inputs are still not fully snapshot-safe. Therefore
the schedule/join topology is useful, but the input ownership contract needs strengthening before it
becomes a general KNEEKURA primitive.

## 11. TLM integration shows the right seam and an unfinished seam

**DIRECT_SOURCE**

Anchor TlmCommonCompatInner:

- detects EntityMaid;
- parses/queues Molang through the maid capability;
- copies the maid YSM model ID onto projectile and vehicle model capabilities;
- broadcasts resulting model info to visible players;
- drives roulette/extra-animation selection from model properties.

For projectile/vehicle propagation, the source contains TODO comments for maid roaming variables and
currently uses an empty float map.

Locator:

- src/main/java/com/elfmcys/yesstevemodel/client/compat/touhoulittlemaid/TlmCommonCompatInner.java

**INFERENCE**

This is directly relevant to the Reimu/TLM work:

- the maid should remain the gameplay/AI authority;
- a YSM adapter should translate maid state into animation/model state;
- projectiles/vehicles can inherit presentation identity without inheriting the entire maid runtime;
- roaming/custom variables need an explicit copy/snapshot policy.

Do not turn a YSM-compatible maid into a fake Player unless a specific API requires it. Keep
appearance binding separate from gameplay entity identity.

## 12. 2.6.5 network is a different architecture from the FRONTIER

**DIRECT_SOURCE**

Anchor NetworkHandler uses a Forge SimpleChannel with protocol version 2.6.0 and explicit message
registration.

Anchor ServerModelManager includes a native-backed model sync path and a worker-side send loop that
observes Netty outbound pending bytes before sending. It waits/retries on send completion.

This is a release-line architecture fact.

**INFERENCE**

The useful idea is **backpressure-aware asset distribution**. The exact sleep/retry implementation
should not be copied blindly.

## 13. FRONTIER redesign: stronger ownership boundaries

**OFFICIAL_DOC / DIRECT_SOURCE**

The 3.0-dev frontier makes responsibilities much more explicit.

### Model management

Client and server model services own catalog/session/resource state.
EntityModelBinding keeps an entity bound to a render target without making the entity itself own
global model resources.

### Network

A Forge EventNetworkChannel carries typed session/distribution/state/control messages.

The architecture distinguishes:

- exact connection
- session
- catalog publication
- content activation
- one server-global ResourceDispatchWorker
- owner-thread publication

A new connection does not inherit an old connection's transfer/publication state.

### Rendering

The current design is explicitly:

~~~text
Bake -> Extract -> Render
~~~

- Bake: relatively immutable geometry representation.
- Extract: apply current BoneAttribute/pose into ModelState/RenderSchedule.
- Render: produce/commit vertices for the current draw.

### Native boundary

Current docs describe native as a capability layer rather than the owner of model identity,
animation/controller semantics or session lifecycle.

**INFERENCE**

For KNEEKURA, this FRONTIER architecture is a better long-term reference than reproducing every
2.6.5 implementation detail.

## 14. FRONTIER known gaps are valuable negative evidence

**OFFICIAL_DOC**

Current official known-issues documents identify, among others:

- isMoving logic is wrong;
- async evaluation lacks immutable input snapshots;
- controller/Molang once-only behavior lacks full Forge end-to-end validation;
- same-frame RenderContext metadata can be stale;
- animation processor updates are not transactional;
- hot-path Molang performance is not yet measured;
- ysm.sync has limited delivery semantics;
- cross-language BoneAttribute/BakedModel ordering lacks independent golden validation;
- renderer shared scratch is non-reentrant;
- native render failure lacks a fallback output path;
- transparent sorting is only local to one model draw;
- many attachment and first-person paths are not yet fully migrated.

These are not reasons to discard the architecture. They are a ready-made checklist for avoiding the
same mistakes.

## 15. Secondary analysis-team technique: semantic structural mapping

**SECONDARY SOURCE**

YSM Mapping API branch mc/1.20.1 at revision
6a01cdfec45623e39bc7fd890e91066e3507666c contains:

- whole-JAR structure analysis
- symbol registry
- analysis profiles
- structure pattern resolver
- semantic analyzers
- content hashes
- mapping/mixin remapping helpers
- 22 test blobs in the pinned tree

Its own project policy keeps private YSM JARs and private analysis outputs out of the repository.

**INFERENCE**

The broadly reusable technique is:

> When a dependency's internal names are unstable, identify semantic targets from multiple
> structural constraints instead of betting on one class/method name.

For KNEEKURA this can be used for compatibility diagnostics or research tooling without publishing
private artifacts or bypassing protected native/model formats.

## 16. Reusable KNEEKURA design extracted from YSM

A generalized character-presentation stack can be expressed as:

~~~text
Game entity / AI
  |
  | sampled immutable presentation input
  v
EntityPresentationRuntime
  |-- state tracker
  |-- Molang/query context
  |-- controller set
  |-- queued events
  |-- model generation
  v
PoseState / BoneAttributes
  |
  +--> semantic locators -> equipment / attachment adapters
  |
  v
BakedGeometry
  |
  v
ExtractedModelState
  |
  v
Renderer backend
  |
  v
Minecraft draw
~~~

Required hardening beyond current YSM evidence:

1. immutable frame input for off-thread evaluation;
2. deterministic event queue phase and at-most-once semantics;
3. model-generation token on all deferred work;
4. transactional pose update or staging buffer;
5. golden tests for Java/native bone ordering and visibility;
6. per-context render metadata separated from reusable pose;
7. bounded/fallback behavior for renderer failure;
8. measurement-driven animation LOD rather than copied constants;
9. integration adapters outside the generic core;
10. runtime tests with YSM-alone and compatibility-stack scenarios separated.

## 17. Current status

Foundation architecture: **EVIDENCE_BACKED**

Still not complete:

- distributed 2.6.5 binary hash/source equivalence;
- bounded Forge runtime experiments;
- CPU/GPU/frame-time measurements;
- multiplayer model-distribution runtime capture;
- exact Molang query catalog;
- complete compatibility adapter inventory;
- visual golden comparison against Blockbench/vanilla/Iris;
- long-soak memory/lifecycle validation.

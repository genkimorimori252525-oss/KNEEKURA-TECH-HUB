# YSM Chinese-speaking community reconnaissance / obfuscation techniques — 2026-10-05

## 1. Scope

This pass asks a narrow question:

> Is there a technically useful Chinese-speaking public YSM compatibility / analysis community, and
> what reproducible **Java-level** reverse-compatibility techniques can KNEEKURA reuse?

Answer: **yes, clearly**.

The useful public material is not one single "deobfuscation team". It is a network of:

- compatibility-mod maintainers targeting the official 2.6.5 JAR;
- Chinese-language Minecraft technical documentation;
- public issue/crash-log analysis;
- YSM-derived/open-reimplementation projects;
- public reverse-engineering reports.

KNEEKURA deliberately takes only:

- JVM descriptors;
- class/member structural fingerprints;
- event / renderer / capability roles;
- runtime hook observability;
- failure history;
- source-vs-artifact version boundaries.

KNEEKURA does **not** preserve or reproduce:

- VMProtect bypass procedures;
- anti-debug bypass;
- native devirtualization workflows;
- model/container decryption recipes;
- cryptographic keys or modified constants;
- DRM-removal tooling.

## 2. Evidence hierarchy

For this lane:

1. **actual official 2.6.5 JAR contract test / exact descriptor**
2. **actual 2.6.5 runtime log / stack**
3. **official release-line source candidate + history**
4. **readable comparative implementation**
5. **community explanation / wiki**
6. **general discussion**

A comment in a compatibility mod never outranks the same project's executable contract test.

A readable replacement implementation never automatically becomes official-YSM implementation truth.

## 3. High-value Chinese-speaking projects found

### HSZK2017/ysm_epicfight_compat

Pinned revision:

`18db9328132bea921ea49f2125e4c0c319fbb5c8`

Highest-value contribution: **actual-JAR contract verification**.

Its `MixinTargetSignatureTest`:

1. opens `libs/ysm-2.6.5.jar`;
2. parses its own optional YSM Mixins;
3. reads target classes through ASM;
4. verifies exact method **name + JVM descriptor**;
5. requires at least eight obfuscated official-YSM Mixins to be inspected;
6. fails when any target drifts.

The source comment explains why this exists: a Mixin using `require=0` can compile but silently fail
when the target method descriptor changes.

This is a much stronger maintenance pattern than "the game starts, therefore the Mixin works."

### 3SCR1P7/TaczFixes

Pinned revision:

`a2223f838fc4f16ecae0315663b7e0e3ca5d23d4`

The build directly pins:

`libs/ysm-2.6.5-forge+mc1.20.1-release.jar`

Its public YSM bridge exposes exact obfuscated targets for:

- TaCZ item/back-gun transform;
- TaCZ Molang/controller binding;
- generic GeoEntityRenderer pre-mesh pose;
- living GeoReplacedEntityRenderer pre-mesh pose;
- TaCZ animation selection;
- CustomPlayerItemInHandLayer;
- public bone getter/setter aliases.

It also adds **runtime hook diagnostics**:

~~~text
static contract:
    method exists in supported JAR
            |
            v
runtime:
    did held-layer hook actually fire?
    did helper redirect actually fire?
    did pre-mesh pose hook actually fire?
    did RPG selector actually fire?
    did back-gun hook actually fire?
~~~

After a bounded relevant runtime window, missing hooks are reported as likely installed-YSM bytecode
drift.

This is the right complement to static bytecode mapping.

### Aleph-1374/tlm-maid-survival

Pinned revision:

`d264991d5ab68370db953ecec1a491c99b576952`

Provides:

- an exact YSM 2.6.5 Carry On predicate Mixin;
- a reflective fallback to the same owner/member/descriptor;
- real 1.20.1 Forge runtime logs containing obfuscated YSM plugin class names.

This supplied a new confirmed Carry On mapping and a Jade plugin mapping.

### mofeng945/TinkersNewlife

Pinned revision:

`6e7f207759fc3de50969ea2a96d717d2409e7b49`

Records a `javap`-verified YSM 2.6.5 renderer shape:

- vanilla/SRG render override;
- should-show-name override;
- render-name-tag override;
- two calls to the superclass name-tag renderer.

That shape uniquely matches the release-line `CustomPlayerRenderer` role.

### Fox-TerribleCoding/YES_SlashBlade

Useful methodological statement:

- the public next-generation source is semantic comparison only;
- it cannot replace the obfuscated 2.6.5 injection target;
- its own build validation checks every referenced third-party symbol against the target JAR.

This matches KNEEKURA's ANCHOR/source-boundary rule.

## 4. Chinese public knowledge base

### Official YSM Chinese documentation

The official documentation/changelog remains useful for:

- version boundaries;
- supported platforms/loaders;
- compatibility features;
- model distribution behavior;
- known unstable integration areas.

It is product/runtime truth, not an obfuscation map.

### MC百科

MC百科 material around YSM compatibility is useful as reconnaissance.

A particularly useful compatibility write-up explicitly warns that:

- YSM 2.6.5 internals are obfuscated;
- hard-binding to obfuscated class/bone details is version-fragile;
- next-generation public source is not the same thing as the injected 2.6.5 artifact.

KNEEKURA uses those statements as **search guidance**, then confirms targets from source, bytecode
contracts or runtime evidence.

## 5. Dedicated reverse-engineering community exists

Public Chinese-language YSM reverse-engineering/report projects also exist.

This is useful evidence that the ecosystem has independently investigated:

- Java layout;
- JNI/native boundaries;
- model loading;
- networking;
- renderer behavior.

Some of those projects also discuss protection circumvention and model decryption.

Those parts are **outside this KNEEKURA lane**.

The useful lesson is the architectural one:

> the distributed artifact has enough externally visible Java/JNI structure that multiple independent
> projects have been able to build compatibility layers around it.

## 6. Reproducible technique A — actual-JAR descriptor contract

For every hard-coded Mixin:

~~~text
Mixin source
   |
   +-- target owner
   +-- method name
   +-- full JVM descriptor
   |
   v
actual supported YSM JAR
   |
   v
ASM class/method scan
   |
   +-- exactly present -> contract passes
   +-- absent          -> build/test fails
~~~

Do not validate only the method name.

Do not validate only argument count.

Do not validate only a readable reconstruction.

The descriptor is a first-class part of identity.

## 7. Reproducible technique B — runtime hook proof

Static presence does not prove that the path is live.

A compatibility bridge should expose small one-way counters/flags:

- hook entered;
- redirect entered;
- final pose changed;
- expected controller selected;
- expected renderer layer entered.

After a bounded relevant context:

- all expected hooks seen -> compatibility path observed;
- one or more missing -> explicit warning with missing stage names.

This converts "feature silently does nothing" into a diagnosable state.

## 8. Reproducible technique C — discover classes by shape, not name

HSZK's compatibility code demonstrates a stronger pattern for movable classes.

Instead of assuming:

~~~text
com.foo.capability.PlayerCapabilityProvider
~~~

scan YSM's loader-known classes and ask:

> Which class declares a static `Capability<PlayerCapability>` field?

Then cache that holder.

This survived package relocation better than a blind list of known provider names.

General KNEEKURA pattern:

~~~text
loader class inventory
  |
  v
cheap structural predicate
  |
  +-- unique result -> semantic role
  +-- 0 results     -> NOT_FOUND
  +-- >1 result     -> AMBIGUOUS
~~~

## 9. Reproducible technique D — call-chain derivation

The paperdoll mapping is a strong example.

Instead of searching for `renderPlayerOverlay` in an obfuscated JAR:

1. find the only YSM implementation of stable external interface `IGuiOverlay`;
2. inspect its render method;
3. find the one downstream YSM call with the stable paperdoll descriptor;
4. map the called owner/method;
5. validate the full descriptor.

This is often more reliable than trying to "deobfuscate everything."

## 10. Reproducible technique E — ecosystem logs as semantic beacons

Other mods/loaders sometimes print the exact class they discovered.

Examples:

- Forge generated event subscriber frames;
- Jade `Start loading plugin at <class>`;
- Mixin target errors;
- runtime compatibility diagnostics.

These logs can turn an opaque owner into a semantic anchor without touching protected internals.

Rule:

> A third-party log may identify a **role** only when the logger's own semantics are known.

For example, a Jade plugin-loader message plus YSM's unique `@WailaPlugin` implementation is strong
evidence. An arbitrary "loading class" message alone is not.

## 11. Reproducible technique F — readable + obfuscated reflection aliases

TaczFixes uses cached reflection accessors with alternatives such as:

~~~text
readable name
obfuscated 2.6.5 name
~~~

and resolves once per runtime class with `ClassValue`.

Benefits:

- no per-frame method lookup;
- one adapter can survive readable/obfuscated layouts;
- failure can be reported once;
- the semantic alias table itself becomes research evidence.

Do not infer the owner from the alias alone.

A method-name pair proves a semantic member **on the runtime object presented to it**, not the exact
class identity, unless the owner is independently established.

## 12. Reproducible technique G — distinguish three naming systems

Never mix:

1. **YSM obfuscator names**
   - `Oo0Oo0o00O00Oo0OOoOOoooo`

2. **Minecraft/Forge SRG names**
   - `m_7856_`
   - `m_6512_`
   - `m_7392_`
   - `m_7649_`

3. **readable semantic names**
   - `init`
   - `shouldShowName`
   - `render`
   - `renderNameTag`

SRG names are not evidence of YSM's own symbol mapping.

## 13. Failure history A — require=0 silent drift

Bad state:

~~~text
target class still exists
target method descriptor changed
Mixin require=0
        |
        v
no startup crash
no useful method-mismatch proof
feature silently stops working
~~~

Repair:

- actual-JAR signature contract;
- runtime hook proof.

Both are needed.

## 14. Failure history B — version number / mod id is insufficient

Several YSM-family builds can share the same mod ecosystem identity and compatible version range
while exposing different internal layouts.

A compatibility layer that chooses an implementation only from:

- mod ID;
- broad version range;

can silently select the wrong branch.

Repair:

- class-presence / structural fingerprints;
- most-specific discriminator first;
- one central fork/layout verdict;
- all adapters consume that verdict.

## 15. Failure history C — hard-coded probe chain rots

A real compatibility failure came from probing only known capability-provider layouts.

When another YSM-family layout moved the provider package, the feature disabled itself without the
rest of the mod obviously failing.

Repair:

- discover by field/type structure;
- use literal-name fallback only after structural discovery fails.

## 16. Failure history D — comment disagrees with executable evidence

Two useful examples:

### Vehicle replacement helper

A human comment called an obfuscated target `CustomVehicleRenderer`.

The exact method returns boolean.

The release-line `CustomVehicleRenderer.render` returns void.

The boolean descriptor instead matches the replacement helper.

**Descriptor wins.**

### Config screen

A Mixin comment says its fully obfuscated target is not the official release.

The same repository's actual-JAR contract test includes that Mixin in the official 2.6.5 check and
passes it against `libs/ysm-2.6.5.jar`.

**Executable contract wins.**

KNEEKURA rule:

> comments are useful discovery metadata, never final identity evidence.

## 17. Failure history E — Mixin package helper crash

A public compatibility project recorded a subtle Mixin failure:

- injection target was correct;
- Mixin application succeeded;
- helper code lived inside the declared Mixin package;
- injected code referenced that non-Mixin helper;
- the game crashed only when the injected path first executed with `IllegalClassLoadError`.

Repair:

- normal helper classes live outside the declared Mixin package;
- runtime-path exercise remains necessary even when Mixin application succeeds.

## 18. Source/artifact generation drift

This pass strengthened a major finding.

Several actual-2.6.5 compatibility probes use a semantic layout like:

~~~text
AnimatableEntity.getCurrentModel()
AnimatedGeoModel.bones()
AnimatedGeoBone / IBone
ModelPreviewRenderer
TacCompat
TacBinding
TacAnimHandler
~~~

The pinned official version-matched source candidate `f184eda` uses newer/different names or
organization in several of those seams:

~~~text
getLoadedGeoModel()
GeoModelState.boneMap()
RenderUtil paperdoll helper
TACZCompat
TacCtrlBinding
TacCompatInner
~~~

Therefore a version string match is not enough to claim source identity.

KNEEKURA must maintain:

~~~text
DISTRIBUTED ARTIFACT SEMANTICS
        !=
VERSION-MATCHED RELEASE-LINE SOURCE CANDIDATE
        !=
FRONTIER / LATER RECONSTRUCTION
~~~

until an exact binary/source provenance link is proven.

## 19. KNEEKURA recommended resolver pipeline

~~~text
[1] pin exact target artifact
    version + loader + MC + content hash
              |
              v
[2] collect stable external anchors
    Forge events / Minecraft types / interfaces / descriptors
              |
              v
[3] build name-independent class/member fingerprints
              |
              v
[4] derive semantic candidates
              |
      +-------+-------+
      |               |
   exactly 1       0 or >1
      |               |
   STRUCTURAL       NOT_FOUND /
   mapping          AMBIGUOUS
      |
      v
[5] compare readable/source lineage
    without overwriting artifact truth
      |
      v
[6] actual-JAR contract test
      |
      v
[7] bounded runtime hook proof
      |
      v
[8] publish owner+member+descriptor map
    + confidence + provenance + divergence
~~~

## 20. What not to copy

Do not copy community practices that:

- assume a decompiled readable replacement is exact official source;
- key mappings by obfuscated member text alone;
- promote cross-version symbols by similarity;
- use `require=0` with no contract/runtime diagnostics;
- silently pick the first reflection candidate;
- publish private/bundled YSM artifacts into the research repository;
- require bypassing native protection to answer a Java-level compatibility question.

## 21. Current result of this pass

The machine-readable YSM map now contains:

- **55** owner/member mappings;
- **22 CONFIRMED**;
- **33 HIGH**;
- **20** explicit source-artifact-divergence records;
- **0** duplicate owner+member+descriptor identities.

Separate alias surfaces retain:

- **23** animated-bone public method aliases with unresolved exact owner;
- **5** animatable/model/event/context aliases.

Unresolved-owner aliases are intentionally not inflated into confirmed class/member mappings.

## 22. Next evidence that would move the map most

The best next step is not broader internet searching.

It is an authorized structural scan of the user's own official 2.6.5 Forge 1.20.1 JAR that exports
only:

- content hash;
- normalized class fingerprints;
- normalized member fingerprints;
- minimal resolved owner/member/descriptor rows;
- ambiguity diagnostics.

The actual JAR should remain local and outside Git.

That one scan would likely:

- identify the exact AnimatedGeoBone owner;
- promote most of the 23 bone aliases in one batch;
- resolve remaining animatable/model owners;
- verify or reject current HIGH mappings without touching protected native internals.


## Bounded evaluator follow-up

Fresh immutable source inspection covers Anan1a/YSM-molang-functions (creator function scripts,
version unspecified), lin114810/ysm-vivecraft-compat (speculative optional eval hook, YSM2.5.1 /
NeoForge1.21.1), and Fox-TerribleCoding/YES_SlashBlade (precise adjacent animation descriptors,
YSM2.6.5 / NeoForge1.21.1). None confirms the selected Forge1.20.1 evaluator identities.
Zero community-based promotions were made. Pinned revisions, exact file URLs/hashes, provenance
limits and documentation retrieval failures are retained in
[MOLANG-EVALUATION-EVIDENCE-2026-10-05.json](MOLANG-EVALUATION-EVIDENCE-2026-10-05.json); the
source/version comparison is in [MOLANG-EVALUATION-RECOVERY-2026-10-05.md](MOLANG-EVALUATION-RECOVERY-2026-10-05.md).

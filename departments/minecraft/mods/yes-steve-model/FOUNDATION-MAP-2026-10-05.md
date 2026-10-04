# YSM 2.6.5 Vanilla/Java Foundation Map — 2026-10-05

## 1. Purpose

This document is the human-readable entrypoint for the exact distributed YSM 2.6.5 Forge 1.20.1
Java shell.

It answers:

- which major subsystems exist in the obfuscated JAR;
- which recovered semantic classes anchor each subsystem;
- how the subsystems reference each other;
- which apparently-unknown regions are actually bundled third-party libraries;
- which classes are still genuinely unclassified;
- where the next high-value reverse-compatibility work should start.

The machine-readable whole-JAR index is:

- [FOUNDATION-MAP-INDEX-2026-10-05.json](FOUNDATION-MAP-INDEX-2026-10-05.json)

The exact semantic owner/member map is:

- [OBFUSCATION-MAP-2026-10-05.json](OBFUSCATION-MAP-2026-10-05.json)

The Foundation Map is a **structural research map**, not a claim that every unmapped class has been
given an exact readable original name.

## 2. Exact artifact anchor

The map is generated from the official Modrinth artifact:

- version: `2.6.5-forge+mc1.20.1`
- version ID: `Zqooxsd2`
- Minecraft: `1.20.1`
- loader: Forge
- SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`
- SHA-1: `151ac7b24da8beeca1a20864565743cfd77af286`
- exact size: **63,269,843 bytes**
- Java classes: **955**
- Java classfile major: **61 / Java 17**

The distributed JAR is never committed to TECH HUB. It is fetched into temporary CI storage, its
hash is checked, structural evidence is generated, and the JAR is discarded.

## 3. Whole-JAR graph

Current exact graph:

- nodes: **955**
- undirected internal edges: **3,618**
- directed class references observed: **3,823**
- connected components: **19**
- main YSM component: **722 classes**
- bundled Concentus component: **131 classes**
- bundled Gagravarr/VorbisJava component: **86 classes**
- remaining components: **15 singleton classes**
- exact semantic seed classes: **97**

The three large connected components explain nearly the complete Java artifact:

~~~text
955 classes
 |
 +-- 722  YSM / modified embedded-runtime main component
 |
 +-- 131  bundled Concentus / Opus codec component
 |
 +-- 86   bundled Gagravarr / VorbisJava media-container component
 |
 +-- 15   isolated singleton utility/constants/enum/annotation/exception candidates
~~~

The 15 singleton classes have zero internal graph degree. They are kept as UNKNOWN instead of being
forced into a subsystem.

## 4. Domain inventory

| Domain | Classes | Exact semantic seeds | Structurally unresolved |
|---|---:|---:|---:|
| BUNDLED_CONCENTUS | 131 | 1 | 130 |
| BUNDLED_VORBISJAVA | 86 | 2 | 84 |
| MODEL | 9 | 4 | 5 |
| ANIMATION | 40 | 4 | 36 |
| MOLANG | 256 | 31 | 225 |
| RENDERER | 74 | 10 | 64 |
| NETWORK / DISTRIBUTION | 73 | 22 | 51 |
| CAPABILITY / STATE | 51 | 4 | 47 |
| GUI | 42 | 2 | 40 |
| INTEGRATION | 26 | 6 | 20 |
| ENTITY PRESENTATION | 134 | 4 | 130 |
| EVENT / LIFECYCLE | 10 | 4 | 6 |
| UTILITY | 3 | 1 | 2 |
| CORE | 5 | 2 | 3 |
| UNKNOWN singleton | 15 | 0 | 15 |

"Structurally unresolved" does **not** mean the subsystem is unknown. It means those class identities
have not yet been promoted to exact semantic owner names.

For example, the MOLANG domain is structurally very clear even though many individual parser,
runtime-value, AST and variable classes still retain obfuscated names.

## 5. Primary architecture

The exact artifact now supports this Java-side architecture:

~~~text
Minecraft Entity / Player / Maid / Projectile / Vehicle
                    |
                    v
       Capability / presentation binding
                    |
                    v
 AnimatableEntity / LivingAnimatable / CustomEntity
                    |
          +---------+---------+
          |                   |
          v                   v
   AnimationEvent       MolangContext : IContext
                              |
                    +---------+---------+
                    |                   |
                    v                   v
               YSMBinding           CtrlBinding
               QueryBinding         ContextBinding
                    |                   |
                    +---------+---------+
                              |
                              v
                 IAnimationController
                    /                 \
                   /                   \
                  v                     v
 PredicateBasedController     CompositeAnimationController
                  |
                  v
             pose / queues
                  |
          +-------+--------+
          |                |
          v                v
 AnimatedGeoModel      BoneAnimationQueue
          |
          v
 IBone / AnimatedGeoBone
          |
          v
 NativeRenderer.renderModel(...)
          |
          v
 protected/native geometry backend
~~~

The Java-side semantics are therefore substantially recoverable even though the native backend
remains outside this research lane.

## 6. Network / resource-distribution architecture

The exact Network/Distribution domain is now one of the strongest mapped areas.

Central anchors:

- `NetworkHandler` — degree **47**
- `ServerModelManager` — degree **29**
- `ClientModelManager` — degree **28**

The packet registry is exact-artifact-backed:

~~~text
NetworkHandler
 |
 +-- 1   SyncDataToClient
 +-- 2   SyncDataToServer
 +-- 3   ExecuteMolang
 +-- 4   SyncModelInfo
 +-- 5   SetModelAndTexture
 +-- 6   SyncAuthModels
 +-- 7   SetPlayAnimation
 +-- 8   SyncStarModels
 +-- 9   SetStarModel
 +-- 15  SubmitRoamingVarsChanges
 +-- 16  SyncProjectileModelInfo
 +-- 17  SubmitRouletteConfig
 +-- 18  EmitMolangSync
 +-- 19  MolangSync
 +-- 21  DispatchServerDrivenProperty
 +-- 22  SyncVehicleModelInfo
 +-- 23  EmitSwingHand
 +-- 51  ServerInfo
 +-- 52  ClientInfo
~~~

The strongest subsystem edge in the entire final map is:

> **CAPABILITY ↔ NETWORK: 116 edges**

That matches the observed design: model identity, selected texture, roaming variables, animation
state and server-driven properties are all capability-owned state distributed over the network.

The native model-content protocol remains opaque, but the Java transport/session/state envelope is
no longer opaque.

## 7. Molang is the largest semantic subsystem

MOLANG contains **256 classes** and is the largest first-party/modified subsystem in the exact JAR.

Mapped hubs:

- `IContext` — degree **103**
- `YSMBinding` — degree **48**
- `CtrlBinding` — degree **40**
- `QueryBinding` — degree **28**
- `ContextBinding` — degree **28**
- `MolangContext` — degree **23**

This explains why model behavior reaches so many apparently unrelated systems.

Major cross-domain edges include:

- ENTITY_PRESENTATION ↔ MOLANG: **96**
- ANIMATION ↔ MOLANG: **36**
- CAPABILITY ↔ MOLANG: **29**
- MOLANG ↔ NETWORK: **19**
- MOLANG ↔ RENDERER: present as a smaller but direct seam

YSM's Molang layer is not a decorative script parser. It is the presentation-side state/query and
controlled-effect fabric connecting game state, controllers, networking and rendering.

## 8. Entity presentation is the second major hub

Mapped presentation anchors:

- `AnimatableEntity` — degree **41**
- `LivingAnimatable` — degree **38**
- `CustomEntity` — degree **38**
- `CustomPlayerEntity` — degree **27**

Important cross-domain edges:

- ENTITY_PRESENTATION ↔ RENDERER: **86**
- ANIMATION ↔ ENTITY_PRESENTATION: **70**
- CAPABILITY ↔ ENTITY_PRESENTATION: **49**
- ENTITY_PRESENTATION ↔ INTEGRATION: **44**
- ENTITY_PRESENTATION ↔ EVENT_LIFECYCLE: **42**
- ENTITY_PRESENTATION ↔ NETWORK: **31**
- ENTITY_PRESENTATION ↔ GUI: **25**

This strengthens the earlier TLM conclusion: the fundamental reusable primitive is a **presentation
runtime wrapped around a gameplay entity**, not a fake-player architecture.

## 9. Animation core

Current exact semantic anchors:

- `PredicateBasedController` — degree **33**
- `IAnimationController` — degree **17**
- `CompositeAnimationController` — degree **15**
- `BoneAnimationQueue` — degree **11**

The artifact-era controller layout differs from the public version-matched release-line source in
several places. That divergence remains first-class evidence.

The high-value unresolved animation region is now a small, connected controller/runtime cluster
rather than an unknown forest.

The next priority inside ANIMATION is the 18-field / IAnimationController-implementing runtime class
that sits directly beside the recovered controller types.

## 10. Model and bone core

MODEL is small and comparatively well constrained:

- classes: **9**
- semantic seeds: **4**
- average domain score: **0.833399**

Mapped hubs:

- `AnimatedGeoModel` — degree **26**
- `IBone` — degree **17**
- `GeoModel` — degree **12**
- `AnimatedGeoBone` — degree **5**

The complete public bone accessor contract has been recovered and validated against the exact JAR.

This domain is therefore suitable as a stable KNEEKURA reference for:

- semantic bone locators;
- mutable per-frame bone pose;
- matrix/pivot state;
- animation/model separation;
- attachment transforms.

## 11. Renderer

Mapped hubs include:

- `ModelPreviewRenderer` — degree **28**
- `RegisterEntityRenderersEvent` — degree **17**
- `CustomPlayerRenderer` — degree **17**
- `GeoReplacedEntityRenderer` — degree **16**
- `CustomPlayerItemInHandLayer` — degree **10**
- `NativeRenderer` — degree **8**
- `GeoEntityRenderer` — degree **7**

The exact graph confirms that rendering is not one class. It is a layered surface across:

- render registration;
- world-entity replacement;
- first-person/paperdoll/preview contexts;
- held-item attachment;
- Geo-model pose extraction;
- native final geometry submission.

MODEL ↔ RENDERER has **20 direct internal edges**.

## 12. Capability / state

Mapped anchors:

- `PlayerAnimatableCapability` — degree **57**
- `PlayerAnimatableCapabilityProvider` — degree **32**
- `CapabilityEvent` — degree **25**
- `ModelInfoCapability` — degree **20**

The high centrality of `PlayerAnimatableCapability` is expected: it is where presentation runtime,
state tracking, model selection and roaming-variable behavior meet the Minecraft player.

Capability is therefore not merely Forge boilerplate. It is one of the primary YSM state-ownership
boundaries.

## 13. Integrations

Current exact/high-confidence integration anchors include:

- `CustomYsmMaidEntity` — degree **23**
- TaCZ animation handler — degree **12**
- TaCZ compatibility transform layer — degree **10**
- Carry On compatibility — degree **8**
- TaCZ binding — degree **3**
- Jade plugin — degree **1**

TLM remains especially valuable because it demonstrates the non-player entity presentation
architecture directly.

The Foundation Map keeps integration classes separate so third-party compatibility logic does not
become mistaken for generic YSM animation primitives.

## 14. Bundled Concentus component

The 131-class disconnected component is **not 131 unknown YSM classes**.

Evidence:

- component size: **131**
- exact hub:
  `o0o0o0oOooOO0OOOOO00O0O0`
- semantic hub: `org.concentus.Inlines`
- exact hub shape: 247 classfile methods / 2 fields
- upstream Inlines: constructor + approximately 246 primitive arithmetic helpers / 2 fields
- official current YSM NOTICE explicitly declares bundled Concentus source

Foundation domain:

`BUNDLED_CONCENTUS`

It is kept in the artifact map because it is physically present in the JAR, but it must not inflate
the perceived complexity of YSM's own gameplay/presentation architecture.

## 15. Bundled Gagravarr / VorbisJava component

The 86-class disconnected component is likewise an embedded media library.

Recovered anchors:

~~~text
oO00O00OooO00OoOOoo0oooO
    -> org.gagravarr.ogg.HighLevelOggStreamPacket

oOoO00O0O0ooOoOoOOo0oO0O
    -> org.gagravarr.theora.TheoraFile
~~~

The exact Theora class retains the distinctive upstream diagnostic:

`Supplied File is not Theora`

and matches the upstream constructor/I/O/Closeable shape.

Official current YSM NOTICE independently lists the bundled Gagravarr/VorbisJava source component.

Foundation domain:

`BUNDLED_VORBISJAVA`

## 16. The remaining 15 UNKNOWN classes

After separating the two bundled libraries, only **15 / 955** classes remain UNKNOWN.

All 15 have:

- degree: **0**
- no nearest semantic seed
- singleton graph components

Shapes include:

- two enums;
- one annotation;
- one RuntimeException;
- several primitive/static constant-holder-like classes.

Because they have no YSM-internal graph edges, forcing them into Model/Molang/Renderer/etc. would add
false confidence without improving the architecture map.

They are intentionally retained as UNKNOWN.

## 17. Major cross-domain seams

Final strongest seams:

| Domains | Internal edges |
|---|---:|
| CAPABILITY ↔ NETWORK | 116 |
| ENTITY_PRESENTATION ↔ MOLANG | 96 |
| ENTITY_PRESENTATION ↔ RENDERER | 86 |
| ANIMATION ↔ ENTITY_PRESENTATION | 70 |
| CAPABILITY ↔ ENTITY_PRESENTATION | 49 |
| GUI ↔ NETWORK | 45 |
| ENTITY_PRESENTATION ↔ INTEGRATION | 44 |
| ENTITY_PRESENTATION ↔ EVENT_LIFECYCLE | 42 |
| CORE ↔ ENTITY_PRESENTATION | 41 |
| ANIMATION ↔ MOLANG | 36 |
| NETWORK ↔ RENDERER | 32 |
| CAPABILITY ↔ RENDERER | 31 |
| ENTITY_PRESENTATION ↔ NETWORK | 31 |
| CAPABILITY ↔ MOLANG | 29 |
| ENTITY_PRESENTATION ↔ GUI | 25 |
| GUI ↔ RENDERER | 25 |
| CAPABILITY ↔ GUI | 22 |
| MODEL ↔ RENDERER | 20 |
| MOLANG ↔ NETWORK | 19 |
| INTEGRATION ↔ RENDERER | 13 |

This is more useful than a package tree because it exposes the real coupling structure of the
distributed artifact.

## 18. How to use the index

Each class entry in the compact index contains:

- obfuscated class name;
- proposed structural domain;
- domain score;
- margin to the second-best domain;
- whether it is a semantic seed;
- graph degree;
- mapped-neighbor count;
- unresolved-priority score;
- connected-component ID;
- superclass and interfaces.

For future reverse-compatibility work:

1. choose one domain;
2. sort its unresolved classes by priority;
3. inspect the top class's exact descriptor/constant/interface shape;
4. compare against source/readable implementations;
5. only promote when evidence is unique;
6. add the semantic class to OBFUSCATION-MAP;
7. regenerate this Foundation Map.

Thus the map becomes progressively more precise without requiring a complete one-shot decompilation.

## 19. Evidence boundary

This Foundation Map establishes:

- complete class coverage of the exact distributed Java artifact;
- exact graph structure for YSM-internal type relationships;
- exact semantic seed classes for recovered mappings;
- high-confidence structural domain propagation;
- two identified bundled-media components;
- an explicit list of truly unclassified singleton classes.

It does **not** establish:

- a readable exact original name for every class;
- exact source provenance for the whole distributed artifact;
- protected native implementation details;
- native model-sync wire protocol internals;
- encrypted model/container internals.

Those boundaries remain unchanged.

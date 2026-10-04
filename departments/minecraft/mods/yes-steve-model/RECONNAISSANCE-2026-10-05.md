# YSM reconnaissance — official issues, analysis teams and community reports

Research date: 2026-10-05

## 1. Purpose

Reconnaissance does not establish implementation truth.

Its job is to answer:

- what users actually try to do;
- which integration combinations fail in the field;
- which symptoms deserve source/history/runtime investigation;
- which independent technical teams have already built robust tooling around YSM.

Promotion rule:

~~~text
community hint
   -> source/history search
   -> issue/commit relation
   -> bounded runtime test if needed
   -> evidence-backed conclusion
~~~

## 2. Official release reconnaissance

Official Modrinth 2.6.5-forge+mc1.20.1 reports:

### Performance / renderer

- long-runtime freeze fix on Linux/Android;
- renderer scheduling improvements;
- opaque rendering optimization;
- model memory-management improvements;
- explicit warning that semi-transparent textures reduce rendering efficiency significantly.

### Compatibility

- linked-mod features are disabled when the linked mod is too old instead of crashing;
- config switches can disable high-risk integrations such as Sophisticated Backpacks / Parkour.

### Animation / model behavior

- some Molang events not firing fixed;
- minecart pitch fix;
- preview/paper-doll rotation fixes;
- katana/TaCZ animation fixes;
- maid clipping through entertainment blocks fixed;
- lance animation category added.

Distribution URL:

- https://modrinth.com/mod/yes-steve-model/version/2.6.5-forge%2Bmc1.20.1

This changelog was used to choose commit-history targets; it is not used as a substitute for code.

## 3. Official issue reconnaissance

### Issue #444 — dedicated-server model sync stalls after index publication

URL:

- https://github.com/YesSteveModel/YSM-Wiki-Issues/issues/444

Reported environment:

- YSM 2.6.5 Forge 1.20.1
- two different dedicated-server environments
- client receives server_index
- server cache contains model payloads
- client session directory exists but remains empty
- previous sessions in the same pack had succeeded

Status in this research:

- **COMMUNITY_HINT**
- open
- no confirmed root cause
- no repair commit linked

Research value:

This is a strong probe for the boundary:

~~~text
session accepted
  -> catalog/index published
  -> content requested/admitted
  -> content transferred
  -> decoded/built
  -> render target activated
~~~

The FRONTIER architecture now models several of these as distinct states, which is exactly the
direction KNEEKURA should use.

### Other issue themes worth retaining as hypotheses

Searches of the official issue tracker surfaced reports around:

- roaming variable loss on model reload;
- Molang/controller multi-animation semantics;
- ground-speed query mismatches;
- negative-coordinate block queries;
- nested custom-function argument handling;
- long-expression/parser failure/log spam.

These are **not yet promoted**. They are candidates for later focused source/history passes.

## 4. Independent analysis team: YSM Mapping API

Repository:

- https://github.com/sakuraimikoto33/YSM-Mapping-API

Pinned Minecraft 1.20.1 branch:

- mc/1.20.1
- revision 6a01cdfec45623e39bc7fd890e91066e3507666c
- 265 tree entries
- 142 blobs
- 83 Java files
- 22 test blobs

Notable public components:

- AnalysisProfile
- JarStructureAnalyzer
- WholeJarStructureAnalyzer
- StructurePatternResolver
- semantic analyzers
- typed symbol registry
- content hashes
- runtime mapping/remapping layer
- loader-specific adapters
- 1.20.1 analysis profile

The project explicitly separates private fixture/JAR handling from committed public source and does
not commit private YSM artifacts or analysis outputs.

### Technique recovered

Do not identify a private/internal dependency solely by one obfuscated name.

Instead combine constraints such as:

- type shape;
- inheritance/interface shape;
- method descriptors;
- field relationships;
- call graph / structural neighborhood;
- known semantic behavior;
- content hash/profile where appropriate.

Then resolve to a typed semantic symbol with an explicit resolution status.

### KNEEKURA use

This technique is useful for:

- compatibility diagnostics;
- tracking renamed internals;
- verifying integration assumptions across revisions;
- opaque Java libraries where source is unavailable.

It is **not** a reason to bypass YSM native protection or model encryption.

## 5. Independent integration team: YSM EpicFight Compat

Repository:

- https://github.com/sakuraimikoto33/YSM-EpicFight-Compat
- pinned observed revision: 16d9a81b4ccbea6c6e9867272121c016d22d7ac2

Role here:

**SECONDARY_INTEGRATION_SEAM_REFERENCE**

Research value:

External compatibility projects reveal which YSM surfaces are actually usable by another animation
system. They are especially useful for distinguishing:

- gameplay mechanics owned by the combat mod;
- model/animation presentation owned by YSM;
- translation state owned by the compatibility adapter.

No behavior from this project is promoted to an official-YSM fact without matching official source
or runtime evidence.

## 6. Comparative implementation: OpenYSM

Repository:

- https://github.com/OpenYSM/OpenYSM
- 1.20.1-forge revision observed: a515d44686af77155a311b2a592327ca5d45a658

Role:

**COMPARATIVE_ONLY**

OpenYSM is useful for seeing alternative design choices and compatibility failure patterns.
Its project material also discusses prior work on YSM encryption/decryption/re-rendering.

KNEEKURA therefore applies a hard boundary:

- do not use it to claim official YSM implementation facts;
- do not copy protection-bypass/decryption techniques;
- do not commit decrypted/protected artifacts;
- only retain safe architectural comparisons and public compatibility lessons.

## 7. Reddit reconnaissance

Reddit evidence is deliberately weak and is stored only as behavior/UX hints.

### A. Model authoring confusion -> Blockbench workflow

Thread:

- https://www.reddit.com/r/MinecraftMod/comments/1bwmty3

A user initially tried to reason from raw model/config numbers, then recognized the Blockbench
workflow.

Research implication:

- preserve a model-authoring test fixture created through the normal Blockbench/YSM workflow;
- do not treat raw hand-edited internal files as the canonical authoring path.

### B. Real community models use Blockbench + YSM 1.20.1

Thread:

- https://www.reddit.com/r/internecioncube/comments/1ob273q

The author describes a community model made in Blockbench for YSM on Minecraft 1.20.1.

Research implication:

- Blockbench should be one visual-golden reference in later runtime verification.

### C. TLM + YSM is a real user workflow

Threads:

- https://www.reddit.com/r/feedthebeast/comments/1mofzqb/does_anyone_know_where_i_can_find_this_model_of/
- https://www.reddit.com/r/Genshin_Impact/comments/1j9qkhr

Users describe loading YSM models and applying them to Touhou Little Maid entities.

Research implication:

- TLM integration is not an edge curiosity; preserve it as a first-class compatibility test target.

### D. Performance complaint on Forge 1.20.1

Thread:

- https://www.reddit.com/r/ModdedMinecraft/comments/1nsuexh

A user reports slowdown/menu crashes after adding YSM, with launcher guidance pointing toward memory.

Status:

- **UNVERIFIED SYMPTOM**
- not proof of a YSM leak or renderer bug.

Research implication:

Later performance testing must separate:

- model geometry/texture size;
- transparency;
- model count;
- memory allocation;
- animation update cost;
- compatibility stack.

### E. Animation-stack false attribution

Thread:

- https://www.reddit.com/r/MinecraftMod/comments/1w89fvj/help_me_plsss_0/

The user had a large stack of animation/model mods including YSM. After troubleshooting, the reported
culprit was another animation mod.

Research implication:

Compatibility tests must be layered:

1. vanilla + YSM;
2. YSM + one integration;
3. YSM + TLM;
4. YSM + combat/first-person stack;
5. full modpack only after smaller layers are clean.

A symptom observed in a full stack must not be attributed to YSM without reduction.

## 8. Reconnaissance-derived test matrix

| Scenario | Why |
|---|---|
| YSM alone, one simple opaque model | establish renderer/animation baseline |
| same model with translucency | measure the documented slow path |
| near / far / culled entity | validate animation update LOD behavior |
| inventory / paper doll / world / shadow / first-person | exercise render-context separation |
| model hot reload | exercise reset ownership and event retention |
| malformed model that fails build | verify terminal failure, no sync hang |
| TLM maid with YSM model | first-class entity-integration path |
| maid projectile / vehicle inheritance | validate model-ID propagation and roaming policy |
| YSM + Better Combat | isolate first-person compatibility |
| dedicated server sync | separate index/catalog publication from payload activation |
| long soak with model swaps | memory/lifecycle validation |

## 9. Confidence grading

### Primary

- official pinned source
- official commit history
- official architecture/status docs
- official distribution metadata

### Secondary

- YSM Mapping API
- YSM EpicFight Compat
- official issue reports

### Recon only

- Reddit
- general community guides
- OpenYSM behavior comparisons

No claim is promoted merely because multiple community sources repeat it.

## 10. Next evidence frontier

The most valuable next step is not more broad web searching.

It is bounded evidence acquisition against the current map:

1. enumerate Molang/query surface from the 2.6.5 source candidate;
2. map TLM adapter state inputs and animation predicates end-to-end;
3. map native JNI method contracts without entering protected native internals;
4. design LAB fixtures for render context, hot reload and dedicated-server distribution;
5. only then run bounded runtime tests.

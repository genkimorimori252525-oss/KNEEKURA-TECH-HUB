# Connector ANCHOR: bounded failure / repair history

## Results

Two cases were traced against Minecraft 1.20.1 / Forge ANCHOR `7f68ac02291fde986119a3f5cab85436bed5c350`. The first is a repair → regression → repair chain: excluding wrong-side mods too early broke nested-dependency discovery, so environment filtering moved after dependency resolution. The second is a narrow Mixin regex-selector remapping fix. Both are historical research; neither is a runtime pass.

The structured companion is [FAILURE-REPAIR-HISTORY.json](FAILURE-REPAIR-HISTORY.json). Its history import is **PARTIAL**, with two cases, zero canonical writes, and `runtime_attestation: false`. Missing upstream logs and deferred reproduction remain explicit.

## Bounded scope and evidence capture

- Seed inventory: GitHub commits endpoint at the exact ANCHOR, `per_page=100&page=1`. This returned 100 objects, from 2026-09-13 through 2024-03-03 in the captured page. Pages 2 onward were not requested; this is not an all-history review
- Follow-up inventories: the old `dev/su5ed/sinytra/connector/locator/ConnectorLocator.java` path returned 40 entries at a 100-entry page bound; the new `org/sinytra/connector/locator/ConnectorLocator.java` path returned one entry at a 20-entry bound. Those inventories located the later environment-filter change
- Deep scope: #904 / #924 → PR #926 → #991 and its follow-up commit; separately #993 and its exact repair commit. The selected parent/after source files and relevant ANCHOR source were read
- Other first-page commits, older general history, broader #88 / aggregate #908, full external-mod artifacts, binary/source equivalence, release/CI proof and NeoForge/FRONTIER history are excluded or deferred
- Capture: 35 primary-source documents, 1,311,321 bytes. Each has a UTC capture timestamp, SHA-256, immutable index snapshot and document ID in the structured companion's evidence entries. Issue/PR text URLs are mutable; their captured content hashes identify what was actually read
- Raw issue/PR JSON and logs stay in private scratch/CAS. The readable analysis is the minimized deliverable; do not publish the raw captures

Exact queries, pagination and exclusions are in the JSON scope. API response content returned through the GitHub connector is captured as exact UTF-8 returned text; this is not a claim to have preserved HTTP headers or original wire serialization. Direct Gist/log downloads are labeled HTTP response-body bytes.

## Case 1: side filtering that hid nested dependencies

### Reported environment and symptoms

AUTHOR_CLAIM: #904 reports a Forge 1.20.1 dedicated server freezing with BCLib after updating Connector beta.37 to beta.39. Exact BCLib / Forge / Java versions were not established for that report. [Issue #904](https://github.com/Sinytra/Connector/issues/904)

AUTHOR_CLAIM: #924 reports C2ME failing on a dedicated server while Connector loads a client-only JiJ module. The captured reporter log identifies Connector beta.39, Forge 47.1.3, Java 17.0.10, Linux amd64 and C2ME 0.2.0+alpha.11.0. It records transformation of `c2me-client-uncapvd`, then an attempt to resolve client `Options` on DEDICATED_SERVER. Observing this external log is not our reproduction. [Issue #924](https://github.com/Sinytra/Connector/issues/924), [revision-pinned reporter log](https://gist.github.com/heipiao233/f337fad5c024525399f335c08111a9af/raw/c3af243398860ad69a5d9b6807a5e09bb30aab2e/debug.log)

The original BCLib log at `mclo.gs/JxVObeG` is unavailable: a direct capture returned HTTP 404 and web retrieval also failed. #924 comments originally call the issue a duplicate of broader C2ME issue #88, while its reporter disputes that classification. This record establishes no blanket C2ME compatibility claim. [Issue #924 discussion](https://github.com/Sinytra/Connector/issues/924#issuecomment-2011974457)

### Earlier claimed repair was disputed

DIRECT_OBSERVATION: commit `2bc9aeec8dfa83b7e89cc550f000617054c12c97` adds the CLASS_TRANSFORMS loop for non-Mixin classes and says it fixes #904. AUTHOR_CLAIM: a later commenter and PR #926 author state that this does not fix the actual wrong-side-mod problem. The #904 timeline records closure against the earlier commit and a later reference to #926; closure alone cannot select the final repair. [Earlier repair diff](https://github.com/Sinytra/Connector/commit/2bc9aeec8dfa83b7e89cc550f000617054c12c97), [contrary report](https://github.com/Sinytra/Connector/issues/904#issuecomment-2014668257), [PR #926](https://github.com/Sinytra/Connector/pull/926)

### First source-level repair

The exact pair is:

- Before: `c4ee605c7f89aae244c0097c12c0bd3fb4b7f84e`, the repair's immediate parent, not a proven bug-introducing commit
- After: `4b2014653be008e2f6463226f0224c1d1144c087`, the merged #926 repair

DIRECT_OBSERVATION: the pre-fix `shouldIgnoreMod` only rejects disabled/already-loaded IDs. #926 changes it to receive metadata and reject mods whose `loadsInEnvironment` is false. This same predicate is used for roots and recursively discovered nested jars. The PR reviewer explicitly corrects the return value to `true` to stop incompatible loading. [Before predicate](https://github.com/Sinytra/Connector/blob/c4ee605c7f89aae244c0097c12c0bd3fb4b7f84e/src/main/java/dev/su5ed/sinytra/connector/locator/ConnectorLocator.java#L292-L294), [repair diff](https://github.com/Sinytra/Connector/commit/4b2014653be008e2f6463226f0224c1d1144c087), [after predicate](https://github.com/Sinytra/Connector/blob/4b2014653be008e2f6463226f0224c1d1144c087/src/main/java/dev/su5ed/sinytra/connector/locator/ConnectorLocator.java#L293-L297), [review correction](https://github.com/Sinytra/Connector/pull/926#discussion_r1536710224)

INFERENCE: this rejects more than eventual execution. Root filtering happens before child discovery; recursive rejection returns an empty stream before adding the parent–child edge or descending further. Thus a rejected container can hide descendants from dependency resolution. The code supports that mechanism, but does not identify the exact Yttr container/edge from the later report. [Root ordering](https://github.com/Sinytra/Connector/blob/4b2014653be008e2f6463226f0224c1d1144c087/src/main/java/dev/su5ed/sinytra/connector/locator/ConnectorLocator.java#L107-L129), [nested ordering](https://github.com/Sinytra/Connector/blob/4b2014653be008e2f6463226f0224c1d1144c087/src/main/java/dev/su5ed/sinytra/connector/locator/ConnectorLocator.java#L232-L245)

### Regression and later repair

AUTHOR_CLAIM: #991's reporter says beta.41 would not load Yttr's JiJ dependencies and used beta.40 for the attached report. Maintainer Su5eD explicitly says he encountered the same problem and attributes it to a regression introduced by #926. This is stronger evidence than inferring a regression from code alone, but is still an author statement rather than a controlled before/after run. [Issue #991](https://github.com/Sinytra/Connector/issues/991), [maintainer attribution](https://github.com/Sinytra/Connector/issues/991#issuecomment-2043604217)

The exact later pair is:

- Before: `34d620665f525e57273cc3dac7da76b653b21949`
- After: `96cdbd49a2fb1ef81657f40431f7a59e7b18dcbd`

DIRECT_OBSERVATION: this later commit removes environment filtering from `ConnectorLocator.shouldIgnoreMod` and adds it to `DependencyResolver.resolveDependencies`, after `ModResolver.resolve`, inverse candidate-to-jar lookup and null filtering. Its separate EnvironmentInterface stripping change is preserved in the diff but is not conflated with the whole-mod JiJ fix. [Later diff](https://github.com/Sinytra/Connector/commit/96cdbd49a2fb1ef81657f40431f7a59e7b18dcbd), [pre-repair resolver](https://github.com/Sinytra/Connector/blob/34d620665f525e57273cc3dac7da76b653b21949/src/main/java/dev/su5ed/sinytra/connector/locator/DependencyResolver.java#L66-L74), [post-repair resolver](https://github.com/Sinytra/Connector/blob/96cdbd49a2fb1ef81657f40431f7a59e7b18dcbd/src/main/java/dev/su5ed/sinytra/connector/locator/DependencyResolver.java#L66-L75)

DIRECT_OBSERVATION: the exact beta.50 ANCHOR retains the later architecture. `shouldIgnoreMod` has no environment check; dependency resolution filters by environment; `locateFabricMods` transforms only the returned candidates. [ANCHOR predicate](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java#L319-L322), [ANCHOR resolver](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/DependencyResolver.java#L66-L75), [ANCHOR transform ordering](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/ConnectorLocator.java#L126-L142)

### Narrow lesson and remaining checks

INFERENCE: keep discovery/graph construction separate from final load admission. In this architecture, a container's side restriction must not automatically erase the opportunity to discover nested dependencies. Test side exclusion and nested dependency retention together. This does not imply that every descendant of an incompatible container must always load; final dependency/environment resolution still decides eligibility.

- Reproduction: REPORTED only; fix verification: NOT_RUN
- No test files are added in the inspected #926 / 96cdbd49 diffs. This does not claim there are no tests elsewhere
- Proposed checks: wrong-side roots; client-only nested module with server-safe sibling; needed dependency beneath an incompatible container; multi-level nesting; both physical sides; inspect resolved candidate sets before final startup
- Unknown: exact Yttr/Lib39 jar identities/topology, original bug-introducing commit, controlled post-fix success
- #991 also contains a separate EnvironmentInterface report and disagreement over a Lib39 injection descriptor in the developer environment. Those are retained as limits, not folded into one cause

## Case 2: Mixin descriptor-regex selector remapping

### Report and exact source pair

AUTHOR_CLAIM: Custom LAN 2.3.0 started successfully but crashed when selecting Create New World. The report specifies Connector beta.41, Forgified Fabric API 0.92.0+1.11.5, Connector Extras 1.10.0 and Cloth Config 11.1.118-forge on Minecraft 1.20.1; it says the crash still happened without Extras. Exact Forge and Java versions were not established. [Issue #993](https://github.com/Sinytra/Connector/issues/993)

The linked crash Gist is unavailable. Public Gist API returned HTTP 404, and web retrieval also failed. Therefore no precise exception, target method or original selector bytes are asserted.

- Before: `96cdbd49a2fb1ef81657f40431f7a59e7b18dcbd`, immediate repair parent
- After: `84fb91456cb0aade0f0d44e4d4a4e925e0f47f5e`

DIRECT_OBSERVATION: the repair commit explicitly links #993 and adds support for regex Mixin specifiers. Before it, visible method annotations directly use the generic conditional annotation remapping path. After it, they route through `processMixinAnnotation`. [Repair diff](https://github.com/Sinytra/Connector/commit/84fb91456cb0aade0f0d44e4d4a4e925e0f47f5e), [before source](https://github.com/Sinytra/Connector/blob/96cdbd49a2fb1ef81657f40431f7a59e7b18dcbd/src/main/java/dev/su5ed/sinytra/connector/transformer/OptimizedRenamingTransformer.java#L77-L88), [after source](https://github.com/Sinytra/Connector/blob/84fb91456cb0aade0f0d44e4d4a4e925e0f47f5e/src/main/java/dev/su5ed/sinytra/connector/transformer/OptimizedRenamingTransformer.java#L79-L125)

### Actual patch semantics

DIRECT_OBSERVATION: the new branch runs when the annotation's `method` list has one item beginning `desc=`. A regex captures a slash-escaped intermediary `net/minecraft/class_` token with four digits. It unescapes separators for `flatMappings.map`, re-escapes the mapped name, and substitutes the captured token into the original selector. The pre-existing generic `remapRefs` / explicit `remap=false` gate remains afterward; the regex branch is outside that gate. [Pattern and implementation](https://github.com/Sinytra/Connector/blob/84fb91456cb0aade0f0d44e4d4a4e925e0f47f5e/src/main/java/dev/su5ed/sinytra/connector/transformer/OptimizedRenamingTransformer.java#L45-L51), [branch ordering](https://github.com/Sinytra/Connector/blob/84fb91456cb0aade0f0d44e4d4a4e925e0f47f5e/src/main/java/dev/su5ed/sinytra/connector/transformer/OptimizedRenamingTransformer.java#L102-L125)

INFERENCE: the repair addresses a namespace-bearing class token embedded in a representation the generic mapper did not explicitly handle. Such a remaining intermediary token could cause a selector mismatch after ordinary class remapping. The lost log prevents proving this exact causal chain for the reported crash.

DIRECT_OBSERVATION: this pattern and method body remain at the exact ANCHOR under `org.sinytra.connector`. [ANCHOR implementation](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/transformer/OptimizedRenamingTransformer.java#L102-L125)

### Narrow lesson and remaining checks

INFERENCE: selector grammar and escaping are part of a remapper's contract. Do not call this general regex support: the actual code gates on one `desc=` list entry and captures one class-name group. Its four-digit pattern has no trailing numeric boundary, so safety for longer class IDs cannot be inferred; multiple distinct class tokens likewise need separate verification.

- Reproduction: REPORTED recipe only; fix verification: NOT_RUN
- The repair changes one transformer source file and adds no test file
- Proposed tests: escaped selector with mapped/unmapped token; multiple distinct tokens; longer numeric IDs; multiple method entries; other selector forms; `remapRefs` and explicit `remap=false` combinations
- No build, Java execution, Minecraft launch or upstream script was performed

## Imported artifact and verification

- Evidence index: `77ab5e20fc41095d4493bb039cabc84d81227db68c6671d25191920328babe10`
- Evidence profile: `255ae2025183a0afc3395c833e002eebefc8dfd21d5b9f113047eb6a09f45952`
- History CAS artifact: `642d3f40c98c3cfab06212aebc5fe27419f5a020e06c2bfec1e3a1609a6138e5`
- 35 captured-document SHA-256 values were checked against both local bytes and their CAS content hashes
- Existing history adapter accepted both cases. Exact ANCHOR + Forge + 1.20.1 queries returned the intended single case for `nested` and `regex`, with no missing captured-evidence IDs
- PARTIAL reflects the declared research coverage and unavailable upstream logs, even though all supplied evidence anchors resolve. Import/query success is not runtime or causal validation

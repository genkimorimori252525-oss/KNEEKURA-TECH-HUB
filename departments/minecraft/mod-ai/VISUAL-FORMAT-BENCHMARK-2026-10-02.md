# Visual format and holding acceptance — 2026-10-02

This is a finite exploratory comparison of eight declared cases. Expectations were retained before the corresponding new photos. The evaluator also prepared the fixtures and knows their expected states: this is not a blinded study, independent model-accuracy estimate or production acceptance. Findings from images are INFERRED; native UUID/state records remain OBSERVED. Final independent branch review is separate.

## Fixed inputs and formats

The new cohort is a protected copy of the user-specified g3 `KNEEKURA_DEBUG_WORLD`: original Tank origin [0,224,0], inner dimensions19×11×19, registered `OBSERVATION_BRIGHT` grid/lightmap. Only four central floor cells, existing selected Maid pose/equipment/flags and observer placement are prepared in the copy. The original world remains unchanged. Texture-missing intentionally uses the already fixed, separately retained old-Golden before run; it is not relabelled as a true-Tank trial.

Each case uses one common immutable native Cardinal-4 set for formats A–E. No new camera capture, modified raw metadata or image synthesis is used to improve a format. Sequential images have `sameFrame: false`. A is the north raw640×480 RGB view, except the explicitly south-only occlusion question. B is all four original views. C is the2×2 contact sheet with direction headers only. D adds subject labels/projected bounds and the retained XZ top-down schematic. E adds the canonical capture's structured facts, selected native timeline and, for the numeric holding question, the SHA-bound registered model bytes. F diagnostic passes are NOT_RUN/unsupported.

Reading amount: A1raw view/307,200pixels; B4raw views/1,228,800pixels; C1sheet/1,274,880pixels including headers; D1annotated sheet plus1schematic; E the same evidence plus explicit facts/timeline. These are input counts, not measured human time or model token cost. D bounds and labels do not prove pixel visibility through occluders. E can answer identity and numeric-state questions that RGB alone cannot establish.

## Expectations fixed before capture

| Case | Question | Declared expectation and independent basis |
|---|---|---|
| Normal | Is the registered staff texture rendered? | YES; fixed model/texture artifact, then native visibility must be inspected |
| Ground burial | Are the subject's feet below floor topY224? | YES; declared y223.4 teleport and stone floor |
| Clipping | Does the subject head intersect the declared stone cell? | YES; posey224 and head cell[9,225,9] |
| Texture missing | Does the held item show the missing-model checker? | YES; pre-existing source model absence and native missing-model warning in old Golden |
| Holding offset | Is `thirdperson_righthand.translation.y` different from final target4? | YES before; source artifacty6, planned aftery4; RGB cannot prove an exact number |
| Obstacle/projectile | Do the declared static arrow and stone obstacle exist? | YES; exact registered UUID/pose and typed block action; no combat-physics claim |
| Occlusion | Is the staff sufficiently visible in the south-only raw view? | NO; pre-capture geometric prediction from the two declared occluder cells; a conflicting image is recorded as a failed prediction |
| RGB ambiguity | Is the arrow the exact registered UUID? | YES by registration/native state; RGB-only answers should remain AMBIGUOUS |

Private expectation artifacts: `K:/kneekura-live-acceptance-20261002/true-tank-fixture/expectations-r7-before-capture.json` and `expectations-b-r3-before-capture.json` (normal uses the successful after cohort). Earlier failed trials and expectation versions remain retained. The declared truth is not rewritten after looking at photos. The normal texture and occlusion rows are fixture predictions whose disagreement must remain visible, not assumed visual truth.

## Native outcome and format judgments

The following are the implementer's finite judgments after inspecting the native raw sets, contact sheets, annotated sheets and selected structured/timeline facts. They are not results of five independent blinded evaluators. A–E use identical source frames per row; F is NOT_RUN for every row. No aggregate accuracy score is assigned.

| Case | A | B | C | D | E | References and unresolved/error mode |
|---|---|---|---|---|---|---|
| Normal | YES | YES | YES | YES | YES | North/east/west show gold/purple staff; south partly occluded. This is an appearance inference, not proof of full loaded resource precedence. |
| Ground burial | YES | YES | YES | YES | YES | Feet disappear into the central stone floor in all four views; native pose y223.4 and floor top224 independently support burial. |
| Clipping | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | Head is covered by stone in all views. E proves entity AABB/stone overlap, but exact transformed head-mesh intersection is not measured. The pre-capture YES expectation remains; it is not silently changed to an occlusion question. |
| Texture missing | YES | YES | YES | YES | YES | Black/magenta checker in all views; old-Golden native missing-model warning and absent item model independently agree. |
| Holding offset | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | YES | Images cannot establish exact JSON y6 versus target4. E proves registered artifact value6; effective loaded numeric transform remains unmeasured. |
| Obstacle/projectile | NOT_VISIBLE | YES | YES | YES | YES | North hides the arrow behind stone; east/west show its thin shaft and south its tip. E identifies exact static arrow/native pose plus VERIFIED stone action. RGB identity is inferred. |
| Occlusion (south only) | NO | NO | NO | NO | NO | South contains at most a small gold sliver, insufficient to inspect the staff. Other directions do not answer this south-only question. NO means insufficient visibility, not item absence. |
| RGB ambiguity (exact UUID) | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | AMBIGUOUS | YES | E proves registered UUID and native entity identity; it does not prove per-pixel UUID segmentation. D's projected B label is structural annotation, not pixel identity evidence. |

The north arrow miss and unresolved clipping/numeric/identity cases are retained failure modes, not forced YES answers. No determinate answer contradicts the retained fixture expectation in this limited inspection, but that is not a blinded false-positive/false-negative measurement. Exact clipping remains unresolved even with E. Native Reimu AABB is [9.199999988079071,224,9.199999988079071]..[9.800000011920929,225.79999995231628,9.800000011920929]; stone occupies [9,225,9]..[10,226,10]. The source model head cube independently predicts intersection, but source geometry is not a loaded/transformed-mesh attestation. The static arrow UUID is `725a5a31-8936-4b63-a4a3-e5cc9a1d2e62`, pose [10.5,224.5,10.5], velocity0, NoGravity/Invulnerable; this is not a combat or projectile-physics trial.

Read-only derived export: `K:/kneekura-live-acceptance-20261002/visual-format-export-r3/manifest.json`. Each case has original-byte SHA-verified raw copies, A–E review HTML, source manifest and derived packet. Canonical native observations and finalization bytes were hash-checked before/after and remain unchanged. E timelines select preceding ACTION_APPLIED/SERVER_ENTITY_STATE rows for the capture's arena epoch; subsequent actions are not presented as pre-capture facts. The XZ schematic shows subject bounds and arena only, not actual block geometry. Earlier partial private exports are retained separately.

| Case | Derived packet SHA256 | Additional E facts/timeline bytes |
|---|---|---:|
| Normal | `c6cdd26e49807cd04720e4713119dc28ce74845162c0df99e045d7355d02edd7` | 334 / 815 |
| Ground burial | `7564450480af87999592ae441c50ea64b255cf494c7d1b71c2e5019e4a558998` | 337 / 3396 |
| Clipping | `7524a4681462380ef837e9a48ff156106b4ef38d18ec5d307ed2eafdc605dd3b` | 334 / 9283 |
| Texture missing | `199f85acc5d5f60d31b67c1ea32c0a1b82ba99d27f905f315f269c5e7ae1e681` | 329 / 815 |
| Holding offset | `c935ce6b444cdbf0e826fbfb9fe69edc63501e500bd6383b326cf07096542974` | 334 / 818 plus registered model bytes |
| Obstacle/projectile | `8b4cefbf73de8d1f3e0b6cedb3be907e27defd24878ff19c02d032a6a5b45864` | 493 / 4080 |
| Occlusion | `f8a958bf64f9e8f14297a0935646dcd63cb31efb89a847c7b41f0c481938f4de` | 334 / 9977 |
| RGB ambiguity | `f53c71ce5be240f6fa98797c32088fc83642bfedcf4e8924e59e934b4edcc663` | 493 / 6555 |

Local recommendation: start with C, one labelled four-direction contact sheet; open raw views for detail and E for exact identity/state/artifact questions. A misses the obstructed arrow. D's boxes do not resolve occlusion or exact mesh intersection and add a second artifact. C reduces four separate image lookups to one; no human-time saving was measured. This recommendation does not modify the production packet default or its provisional benchmark status.

## Actual Blockbench holding comparison

True-Tank `tank-a-r7` (registered displayy6) and `tank-b-r3` (y4) both produced four COMPLETE/RESTORED Cardinal-4 sets, six VERIFIED actions, VERIFIED scoped cleanup, clean stop, zero writer drops/queue and EVIDENCE_COMPLETE. The cross-run comparison of slot0 is MATCHED_EVIDENCE_ONLY / NOT_EVALUATED with no reasons. Only generation1→2 and selected resource hash `5ec7e5bfe395e81d653e8bfbcaa7fa085f1e8d3c74c9294cff790f48394cc007`→`b161675b3aa5bca5bd732c19edf8e9363d3ff0dc75856ce627b420c5a1068165` are declared differences. Registered model changes only `thirdperson_righthand.translation.y`6→4, preserving texture binding and other model/display data. It uses the existing Blockbench repair artifact, not unsupported `use_item`.

Comparison SHA256 `1340e21bc0c60a120cad62af0b77b73e6733f9fcecafcad87c3c5f16edde8532`; inspected paired sheet `25f88736223c4cd6aebd1f69a597e252d3781f8645bce8903343914962f9c62e.png`. North/east/west visibly retain the textured gold/purple staff with a small displacement; south remains partly occluded. This establishes native holding appearance alongside registered numeric change. It does not establish that the new pose is aesthetically superior or that the exact loaded transform equals the registered numeric value. Speech-bubble animation differs between runs, so whole-scene pixel equality is not claimed.

Private `holding-comparison/gold-pixel-roi-analysis.json` retains a simple RGB gold mask: north centroidy315.30→309.96; east centroidx415.43→408.00; west centroidx220.40→226.69. These auxiliary pixel summaries are not mesh segmentation, exact transform proof or a gameplay score. All original images and metadata remain unmodified.

## Verification and limits

The existing compiler/presentation Windows run has20passes and1EPERM symlink-fixture failure. It is not an all-pass result, and its security guard remains intact. The optional Tank recipe contract has19checks, with genuine Forge API compilation; raw images and comparison guards are unchanged. Exact final source verification is recorded after publication.

The production packet's provisional benchmark status remains unchanged. A local recommendation based on these eight exploratory cases cannot freeze a universal packet default or establish general vision accuracy, whole-world equivalence, YSM correctness or gameplay PASS.

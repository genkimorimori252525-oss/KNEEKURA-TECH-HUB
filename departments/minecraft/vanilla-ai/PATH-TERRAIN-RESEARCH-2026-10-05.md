# Path / terrain static research — R64

R64 continues original B4/B5 in [the authorized handoff](../LOCAL-EXECUTION-HANDOFF-2026-10-02.md). It expands [Pathfinding](PATHFINDING.md) and adds [terrain/malus semantics](TERRAIN-MALUS-SEMANTICS-2026-10-05.md), with an additive [method/field/inheritance ledger](PATH-TERRAIN-BYTECODE-LEDGER-2026-10-05.json). It adds no runtime hook or native trial and does not complete the original `/goal`.

## Exact input and extraction

| Identity | Value |
|---|---|
| Minecraft / loader / namespace | 1.20.1 / Forge47.2.0 / Mojmap |
| Artifact stage | `resolved_userdev`, actual mapped development artifact; not pristine vanilla or loaded transformed bytes |
| Artifact SHA256 | `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb` |
| Foundation Map ID | `522cbb565d187f8e1e7b97140206f5ac11e8ca90719528bd661f875f184e34fd` |
| Source index snapshot | `55a63559b62697c11e8ece0cd2fcb97d2db4730684789a31240b2c515f08ba06` |
| JDK provider |17.0.12 `javap -private -s -c -l -verbose`; executable, release and modules hashes reverified |
| Inheritance scan |7,108 exact Minecraft owners; superclass-chain closure, not a class-name suffix filter |
| Family closure, including base |11 Navigation /6 NodeEvaluator /2 PathFinder owners |
| Explanation ledger |31 exact classes /302 selected methods /116 selected fields |

The original class/disassembly hashes were reverified. Sixteen prior whole disassemblies were hash-verified and reused; missing same-artifact bodies were obtained with the same hashed provider. The newly included `Warden$1$1` proves XZ edge distance at the actual override, independently of its outer declaration. All selected method descriptors and line slices match class declarations and the retained whole disassembly. Slice hashes include declaration/descriptor/metadata and are not canonical bytecode-body hashes.

Private Vineflower1.11.2 derived Java aided reading. Its176,831-byte selected/nested-class input, tool and log hashes are retained. Provider exit was0 and24 actual DirectorySaver source files covered the selected outer classes. Forty-eight warnings report inconsistent inner-class access entries; actual class flags/descriptors and bytecode remain authoritative. The first private postprocessor incorrectly expected an output JAR and failed; actual directory outputs were then finalized without rerunning the provider. This is not original-source or decompiled/loaded equivalence proof. No new product dependency was added; class/JAR/whole javap/derived Java and machine paths remain local.

## Required explanation coverage

| Original item | Explanation |
|---|---|
| Navigation families / recompute / execution | All11 owners including anonymous Bee/Warden; Path creation/reuse/adoption, sameAs, strict20-tick recompute interval, waypoint/stuck/trim/control differences |
| Finder / reach / budgets | Public prepare/normal cleanup, null-start/exception limits; fixed visited base/current multiplier, pre-pop budget, Manhattan accuracy, Euclidean range versus virtual edge, weighted heuristic, accepted relaxation and fallback reconstruction |
| NodeEvaluator families / collisions | All6 owners; integer Mob extent, ground steps/falls/AABBs, aerial26 and aquatic10 neighbors, amphibious vertical/shallow rules, Frog special classification |
| Path / Node / Target / BinaryHeap | Actual fields/lifetime/index/membership/predecessor/g-h-f/cost, coordinate-only equality, heap order and closest/reached distinction |
| BlockPathTypes / effective malus | All25 declared defaults, vehicle/custom getter boundaries, five actual constructor examples, amphibious preparation/restoration and additive node costs |
| Hazards / doors / rails | Forge callback precedence, raw/support/neighbor classifications, fence/door/rail policy, volume aggregation and collision independent of enum cost |
| Regional versus evaluated | Static observer query, cached override/default, original getter/node/neighbor/relaxation/returned/adopted/actual-motion separation; no replay or inferred rejection |

The documents describe source semantics, including branches not observed in an existing native trial. Existing finite path/heap/g/closed/returned/edge/malus native records keep their own source/run/identity/cap limitations. R64 does not enlarge those acceptance scopes. A capped prefix or optional unknown field does not require another deep hook solely to appear complete.

## Validation and remaining work

Reverification covers artifact/JDK, all selected class/disassembly hashes, exact descriptors and302 slices, complete inherited families in this artifact,25 enum constructor defaults and critical bytecode call/field boundaries. Relative document links, UTF-8 JSON and the scoped diff are checked before publication. No product behavior changed, so prose-mirroring tests or a new Minecraft run are unnecessary.

B4/B5 now have their detailed static explanation. Required B8 debug-render/precedent research, general Mob catalog/community provenance, FRONTIER comparison reconciliation, true Boss adapter fields, same-case integrated diagnosis, nine separate cost measurements and exactly one final independent whole-diff review remain in the [original reconciliation](ORIGINAL-REQUIREMENT-RECONCILIATION-2026-10-05.md). Draft publication and exact final-HEAD CI are recorded separately; no merge/full acceptance is implied.

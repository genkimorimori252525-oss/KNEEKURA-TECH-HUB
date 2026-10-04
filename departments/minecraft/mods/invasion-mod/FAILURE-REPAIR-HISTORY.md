# Failure / Repair History — Invasion Mod

Status: **PARTIAL bounded review. Runtime reproduction NOT_RUN.**

## Scope

Legacy review is intentionally bounded to the public 1.7.10 history around version 1.1.2 plus the uploaded distributed binary. Modern review is bounded to high-value recent commits in the 1.20.1 branch concerning spawn failure and engineer route recovery. This is not an all-Issues or all-commits crawl.

Legacy head: \`644a52ddea104c206d022bef9edc135c060cba1d\`.

## Case L1 — Pig Engineer DataWatcher indices exceeded the supported range

- before: \`5e19c6638795f0cf5ecdaa724d08fbaceaed878c\`
- after: \`accde83904fd498ef748ed59cfcbe36e8e8d83ea\`
- repair commit message: **“bugfix: datawatcher value over 31.”**
- affected symbol: \`EntityIMPigEngy\`

DIRECT_OBSERVATION: the before revision moves engineer watched fields to indices 32 and 33. The repair moves them to 30 and 31 and updates all corresponding reads/writes.

Repair:
https://github.com/UnstoppableN/Invasion-mod/commit/accde83904fd498ef748ed59cfcbe36e8e8d83ea

Lesson: old entity metadata channels have hard index budgets. Reserve/survey inherited watcher IDs before adding variant state. In modern versions, use current synchronized entity-data APIs and regression-test subclass field allocation.

Reproduction: NOT_RUN. Fix verification: source diff only.

## Case L2 — Tier-3 Zombie Pigman could destroy the Nexus block directly

- before: \`accde83904fd498ef748ed59cfcbe36e8e8d83ea\`
- after: \`86b2a77598c784bc85a2febdac45386990f27bb9\`
- affected symbol: \`EntityIMZombiePigman\`

DIRECT_OBSERVATION: the repair adds \`block != mod_Invasion.blockNexus\` to the charge/destruction path before breaking impacted blocks.

Repair:
https://github.com/UnstoppableN/Invasion-mod/commit/86b2a77598c784bc85a2febdac45386990f27bb9

Lesson: protected-object semantics must be enforced at **every world-edit entry point**, not only the generic TerrainModifier. Impact attacks, explosions, scripted demolition and normal mining need a shared protection predicate.

Reproduction: NOT_RUN. Fix verification: source diff only.

## Case L3 — distributed 1.1.2 has broken Zombie Pigman T2/T3 wave patterns

- state: present in uploaded \`Invasion_1.1.2_1.7.10.jar\`
- source candidate: \`644a52ddea104c206d022bef9edc135c060cba1d\`
- affected symbol: \`IMWaveBuilder\` static pattern initialization

DIRECT_OBSERVATION (source): \`zombiePigmanT2Any\` and \`zombiePigmanT3Any\` are allocated, but calls adding tier 2 and tier 3 are accidentally made on \`zombiePigmanT1Any\`. The T2/T3 objects are then placed in the pattern map without their intended tiers.

DIRECT_OBSERVATION (uploaded bytecode): \`javap -c -p\` shows the T2/T3 objects are stored in separate locals while \`addTier(2)\` and \`addTier(3)\` are invoked on the local holding the T1 object.

Because \`EntityPattern.generateEntityConstruct\` defaults a missing tier selection to 1, the named T2/T3 Pigman patterns fall back to tier 1.

No repair was found inside the bounded original history window. Modern ports use a substantially reworked entity/wave system, so they are not treated as proof of the original fix commit.

Lesson: weighted pattern/table construction needs direct table tests: every named pattern should generate only allowed tiers/flavours and all referenced patterns should be nonempty.

## Case A1 — impossible spawns could leave modern wave accounting stuck

- ANCHOR after revision: \`aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10\`
- immediate parent: \`653af978de40269ed89e023dc8010456c480c5c0\`
- commit: **“Add configurable wave spawn layers and spawn failure recovery”**

DIRECT_OBSERVATION: the repair adds a 30-second spawn-failure grace, explicit pending-spawn discard, \`notifySpawnsSkipped\`, player warning, and tests asserting skipped mobs reduce outstanding phase/wave targets **without increasing kill counts**.

Repair:
https://github.com/kevintrini2811/Invasion-Mod/commit/aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10

Lesson: scheduler completion and combat success are separate accounting domains. If an environment makes a planned spawn impossible, close the scheduling obligation explicitly; never fake a kill to unstick progression.

Reproduction: NOT_RUN. Fix verification: source tests inspected, not executed here.

## Case A2 — engineer tower work competed with ordinary navigation/recovery

Representative repair chain:
- \`c15f552d97ecb89d508c705fc1d0b36dc26b4a80\` reuse/repair existing towers
- \`5bcbe853c3269fe82c43f8e39d9f4336655e1f0f\` share/repair towers across mob types
- \`b292e0ee9adb29cee4446a0c893253af231a5b26\` start repairs promptly and prevent recovery detours
- later follow-up \`6f027de2cba36ac19693ab740e3f71fec1ca3636\`

DIRECT_OBSERVATION at \`b292e0ee...\`: engineer tower ownership blocks ordinary GoToNexus and MineBlock behavior while tower work is active; navigation claims nearby towers before normal recovery; regression tests verify work begins at navigation arrival without starting another path.

Lesson: when a route action owns movement, competing goals must have an explicit exclusion contract. “Same priority” is not enough if vanilla navigation/recovery can restart movement underneath a construction state.

Reproduction: NOT_RUN. Fix verification: tests inspected, not executed.

## Structured history boundary

The companion [FAILURE-REPAIR-HISTORY.json](FAILURE-REPAIR-HISTORY.json) intentionally contains no imported cases yet. The current session retrieved source/diffs through the GitHub connector but did not ingest those captures through the TECH-HUB profile/CAS adapter, so there are no legitimate \`index_snapshot_id\` / \`document_id\` values. Fabricating those IDs would violate the history format. The readable cases above remain research notes until a future capture/import pass binds immutable evidence.

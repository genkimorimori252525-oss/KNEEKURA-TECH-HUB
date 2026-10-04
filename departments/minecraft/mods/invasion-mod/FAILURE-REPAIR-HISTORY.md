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


## Case L4 — Wave 5 finale starts after the Wave has already completed

- state: present in uploaded `Invasion_1.1.2_1.7.10.jar`
- affected symbols: `IMWaveBuilder.generateMainInvasionWave(5)`, `Wave.isComplete`

DIRECT_OBSERVATION (source): the Wave-5 finale is scheduled from 135000 through 165000 ms with amount 7, while the enclosing Wave is constructed with `waveTotalTime=130000`.

DIRECT_OBSERVATION (uploaded bytecode): `javap -c -p` exposes the same constants.

DIRECT_OBSERVATION: legacy `Wave.doNextSpawns` only invokes an entry while total elapsed time is inside the entry's window; `Wave.isComplete` returns true once elapsed exceeds total time.

Result: the seven-mob finale cannot enter its scheduling window through the normal Wave-5 scheduler before the Wave completes.

Lesson: validate every authored entry against the enclosing encounter horizon. A wave compiler/test should reject `entry.begin >= wave.duration` and warn when `entry.end > wave.duration`.

Reproduction: NOT_RUN in Minecraft. Static source + uploaded bytecode confirmation only.

## Case A3 — blocked spawn obligations were hot-looped, then forgotten, then explicitly accounted

Representative repair chain:

- `6bea029c1e182b238bda6a0f3a740755c9a31a61` — back off blocked Nexus spawn retries;
- `bd28a994adaeb85e4ec034b94fe1a8cc219408b6` — retry blocked wave spawns until completion;
- `1589c88f45bd6958441aae2f9747c01a9af8c1ff` — discard pending spawns when a Nexus stops;
- `aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10` — bounded spawn-failure recovery / skipped-spawn accounting.

DIRECT_OBSERVATION: the resulting architecture distinguishes a pending planned spawn from a successful spawn and from a defeated mob. Timed-out impossible spawns reduce outstanding obligations but do not grant kill credit.

Lesson: timed encounter systems need a lifecycle for obligations: pending -> fulfilled, explicitly skipped, or cancelled. “Timer expired” is not sufficient state.

Runtime reproduction: NOT_RUN.

## Case A4 — Burrower movement needed ownership, collision feedback and realized-motion history

Representative repair chain:

- `20ebb2b6608bca3f65dd1dd5d10a455d997d1603`;
- `57d8b6b9f21de18939b8f92b2d77bfc431e0761f`;
- `d40b627f3df86104e9c08c3655911e6b3f6904da`;
- `a03aadef0debf91bfe567f84141e7945fd64505b` / `9f5e2a11f05ff878f3eb91405479a7eed5c83c28`;
- `3512f461b658af2ee4b8823a7a279ad83d062632`.

DIRECT_OBSERVATION across these diffs: fixes repeatedly move Burrower away from predicted/virtual movement and toward actual position, actual collision, explicit maneuver state and client reconstruction from realized motion.

INFERENCE: these repairs express one coherent architectural lesson—custom locomotion that bypasses normal walking assumptions must own movement and use realized collision/motion as feedback. The exact original trigger of every repair was not reproduced.

Runtime reproduction: NOT_RUN.

## Case A5 — flying wall avoidance became a cached committed crossing

Representative commits:

- `946ec1a8e76da6c01d987ee5d2fc46499b6a40fb`;
- `4ba7e71c66c4f280ff13c36362d1a9f42a71aadf`;
- `479269027175c295ae99c03779d2aea915446a94`;
- revert `05a23ad9c3d84ca1509dd7a7334e862afa714b97`;
- restoration `5f209558a091f7fd69669a3e93543a5a2d495039`;
- native-control integration `c8b19f635d354d54734b85381bc879445295921f`.

DIRECT_OBSERVATION: the resulting design extracts `FlyingWallPath`, caches wall/clearance queries, and preserves a waypoint several blocks beyond the wall until the flyer crosses it. Configured flying/jumping mobs are then driven through native movement controls.

UNKNOWN: this bounded pass does not establish why throttling was temporarily reverted and then restored.

Lesson: expensive obstacle discovery and movement commitment are separate concerns—cache discovery, but retain a crossing target long enough for the controller to finish the maneuver.

Runtime reproduction: NOT_RUN.

## Structured history boundary

The companion [FAILURE-REPAIR-HISTORY.json](FAILURE-REPAIR-HISTORY.json) intentionally contains no imported cases yet. The current session retrieved source/diffs through the GitHub connector but did not ingest those captures through the TECH-HUB profile/CAS adapter, so there are no legitimate \`index_snapshot_id\` / \`document_id\` values. Fabricating those IDs would violate the history format. The readable cases above remain research notes until a future capture/import pass binds immutable evidence.

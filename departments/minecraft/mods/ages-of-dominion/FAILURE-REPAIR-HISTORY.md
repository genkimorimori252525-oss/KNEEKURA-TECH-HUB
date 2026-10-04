# Ages of Dominion — bounded failure / repair history

## Scope

This review is deliberately bounded to the only visible source transition in the pinned public
repository:

- before: `04d98a8bae28f9245aa1b992832d245bc1791fcb`
- after: `c1e71a021ba88a053a378292c6011cb89828fd36`
- after commit message: `v4.2.0 bug patch`
- release: public v4.2.0 bug-patch notes

The repository exposes a very small public commit history, so this is not evidence that these are
the only failures that ever existed. No runtime reproduction was performed.

No structured `FAILURE-REPAIR-HISTORY.json` is emitted in this pass because the Hub's structured
history format requires immutable captured document/index IDs from the local evidence adapter.
Those IDs were not created here and are not fabricated.

## Case A — unsafe route fallback and path churn

### Before

DIRECT_OBSERVATION: the earlier `RtsUnitOrders` could keep a nearby fallback coordinate and, when
no reachable Path was obtained, call coordinate navigation anyway. Candidate routes were not
validated node-by-node by a shared terrain safety contract.

### After

DIRECT_OBSERVATION at `c1e71a0`:

- new `RtsNavigationSafety` validates feet/head/support, steps, diagonals and each remaining Path
  node;
- active paths are rechecked;
- no safe path means stop + failed retry backoff;
- nearby path probes remain capped at four;
- villagers can stop a live route immediately when terrain changes.

**Reusable lesson (INFERENCE):** an unreachable RTS target is not permission to bypass navigation.
Fail closed, retain the strategic intent, and retry later. Bound path probes independently from the
number of units.

Runtime verification: **NOT_RUN**.

## Case B — lumberjack target identity drift

AUTHOR_CLAIM: v4.2.0 says lumberjacks could stall on tall/branched jungle trees.

### Repair

DIRECT_OBSERVATION: v4.2 introduces an explicit bounded tree component reservation, raises/codifies
tree scan bounds, keeps the original worksite anchor stable while individual log targets move, and
rebuilds a reservation after reload only when the persisted target/worksite still describes the
same natural component.

It also caps the captured component and prevents protected building timber from entering the tree.

**Reusable lesson (INFERENCE):** a multi-block job needs a stable work-object identity. A mutable
"current block" is not enough when completing that block changes the topology that will be used to
find the next one.

Runtime verification: **NOT_RUN**.

## Case C — mine command accidentally became ordinary selection

AUTHOR_CLAIM: v4.2.0 says a selected worker clicking a mine should be command-only.

### Before

DIRECT_OBSERVATION: the server selection response was first consumed to resolve the pending worker
order, then immediately written back into ordinary building-selection state. The same reply served
two meanings.

### After

DIRECT_OBSERVATION: `ClientPayloadHandlers.handleSelection` records whether the pending unit command
consumed the reply. If it did, ordinary building/construction selection state is cleared and the
handler returns. A normal click with no pending unit order still opens the building panel.

**Reusable lesson (INFERENCE):** when one response can be either an acknowledgement for a pending
command or a normal UI selection, make consumption explicit. Do not let one network message mutate
both state machines accidentally.

Runtime verification: **NOT_RUN**.

## Case D — destructive terrain normalization

The before revision contains `RtsTerrainGeneration`, a world-generation flattening pass intended to
make RTS terrain easier to use.

AUTHOR_CLAIM: the v4.2 commit says this destructive Overworld pass was removed so vanilla relief,
water, caves, ores and structures remain intact.

DIRECT_OBSERVATION: the class and old generation mixin are removed. The new code instead adds
terrain profiling, safer path validation and more robust placement/tree logic.

**Reusable lesson (INFERENCE):** do not globally rewrite the world to compensate for weak unit
navigation/placement. Prefer local adaptation: terrain-aware navigation, bounded work-point search,
placement validation and a camera that follows terrain.

Runtime verification: **NOT_RUN**.

## Case E — semantic tree detection

DIRECT_OBSERVATION: v4.2 adds `NaturalTreeClassifier`, a bounded topology/environment classifier.
A log tag alone was unsafe because authored structures also use logs.

The classifier requires root context and canopy evidence and respects protected structures.

**Reusable lesson (INFERENCE):** resource tags describe block categories, not object ownership or
world semantics. Destructive automation needs a stronger predicate than `#logs`.

Runtime verification: **NOT_RUN**.

## Case F — melon parity

AUTHOR_CLAIM: v4.2.0 makes full melons pumpkin-equivalent worksites, yielding exactly 4 Wood + 1
Food while stems/carved pumpkins remain unchanged.

DIRECT_OBSERVATION: current worker classification treats full pumpkin/melon blocks as explicit
single-block worksites and separates wood/food yield helpers from tree-component logic.

**Reusable lesson (INFERENCE):** exceptional single-block resources should be represented as an
explicit worksite type rather than forced through a connected-tree algorithm.

Runtime verification: **NOT_RUN**.

## Coverage limits

Inspected:

- exact v4.0 -> v4.2 Git compare;
- before/after source for order/path and selection handling;
- current worker/tree/navigation/building implementation;
- v4.2 release notes.

Not established:

- bug-introducing revisions before the visible v4.0 snapshot;
- issue/PR discussion chains;
- real-game reproduction;
- CI/test evidence;
- released JAR ↔ source compiled equivalence;
- performance numbers.

The repair history is therefore **PARTIAL / REVIEWED_BOUNDED_DIFF**, not whole-history proof.

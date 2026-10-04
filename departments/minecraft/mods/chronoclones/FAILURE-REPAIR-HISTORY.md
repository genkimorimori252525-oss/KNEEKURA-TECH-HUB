# Chronoclones — bounded failure / repair reconnaissance

## Scope

This is a **partial** history pass for the clone/replay subsystem, bounded to the publicly
retrievable 0.9.0, 1.0 and 1.1 release notes plus the maintained CurseForge issue surface.

It is not an all-history review and does not satisfy whole-target
`EVIDENCE_BACKED` failure/repair coverage.

## Evidence availability

- The CurseForge legacy issue surface returned no issue records during this pass.
- The project pages link an issue tracker but no public source repository was found in the official
  links or bounded search.
- Therefore no Issue -> PR -> commit -> before/after source chain could be verified.
- Release-note fixes below are **AUTHOR_CLAIM**, not reproduced fixes.
- No structured `FAILURE-REPAIR-HISTORY.json` is emitted yet because the current pass lacks the
  immutable captured document/index IDs required by the Hub's history schema. Inventing those IDs
  would violate the provenance contract.

## High-value author-recorded repair groups

### A. Save/unload/edit persistence

1.1 reports fixes for clones losing held items/ammo during save, unload or edit, and adds resume
where a clone left off after reload.

**Transferable lesson (INFERENCE):** routine definition, actor inventory, execution cursor and
in-flight action state must be explicit persistence domains. Test save/unload/edit/reload at
different action phases rather than only between loops.

### B. Long-action lifecycle

1.1 reports "long actions never finishing in short routines."

**Transferable lesson (INFERENCE):** action completion cannot be keyed only to routine wrap/end.
Long actions need their own bounded lifecycle and timeout.

### C. Spatial policy enforcement

1.1 reports clones acting outside the configured max radius.

**Transferable lesson (INFERENCE):** validate authority at execution time. Editor/record-time
validation alone cannot prevent stale or transformed actions from escaping a sandbox.

### D. Player-like item semantics

1.1 reports tool durability, used-tool Exact matching, enchanting, held item/ammo, and XP repairs.

**Transferable lesson (INFERENCE):** a player-semantic executor inherits mutable state and vanilla
edge cases. Item identity matching must be separated from mutable damage/wear. Inventory, XP and
transaction state need regression coverage.

### E. Lifecycle/privacy/policy

1.1 reports recorder state persisting incorrectly across logout, goggles exposing other players'
routines when disabled, and clones damaging players with PvP off.

**Transferable lesson (INFERENCE):** owner/session lifecycle, visibility policy and mutation
permission checks belong at authoritative boundaries, not only UI state.

### F. Inactive automation

1.1 reports hoppers filling inventories of inactive clones.

**Transferable lesson (INFERENCE):** entity/block capabilities exposed to external automation need
an active-state gate or a deliberately documented dormant behavior.

### G. Scheduler/energy edge

1.1 reports Anchor stuttering at low charge.

**Transferable lesson (INFERENCE):** resource depletion and scheduler clocks should have explicit
transition semantics. A low-resource state should not oscillate implicitly between progress and
stall.

## Earlier release clues

0.9.0 reports:

- items disappearing in an empty Anchor;
- fuel/upgrade slots accepting wrong items;
- preview flicker while nudging;
- improved dedicated-server stability.

1.0 reports:

- clones unable to pick berries;
- a multi-loader/version refactor.

These are useful search seeds for later bytecode/source analysis, but no causes or exact repairs are
claimed here.

## Remaining history work

If a later pass can acquire the exact 1.20.1 JAR or a public source snapshot, the next bounded
history questions are:

1. locate persistence code corresponding to 1.1 save/unload/edit repairs;
2. identify long-action scheduler state and the 1.1 repair;
3. identify radius/PvP checks at the final action execution seam;
4. identify item-matching semantics changed for used tools;
5. identify inactive inventory capability gating;
6. compare ANCHOR and FRONTIER implementations without assuming release-number equivalence.

Source URLs are listed in
[CLONE-REPLAY-RESEARCH-2026-10-04.md](CLONE-REPLAY-RESEARCH-2026-10-04.md).

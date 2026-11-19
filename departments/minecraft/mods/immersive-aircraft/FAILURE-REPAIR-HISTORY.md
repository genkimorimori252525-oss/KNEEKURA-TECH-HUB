# Immersive Aircraft — Failure / Repair History

## Scope

Track: **ANCHOR — Minecraft 1.20.1 + Forge 1.3.3**

Selected bounded window:

- 1.3.0 -> 1.3.2 -> 1.3.3 source tags and public release notes;
- selected physics/data issue #266 because it directly affects interpretation of aircraft stats;
- no attempt to scan every historical issue.

Status: **PARTIAL**.

The source commits/diffs were inspected live through GitHub, but the Issue/release payloads have not
been captured into the Tech Hub profile/CAS history adapter in this session. Therefore the
machine-readable companion remains a PARTIAL scope inventory rather than pretending these are fully
imported canonical history cases.

## H1 — Forge Bamboo Hopper sinking fix

Public 1.3.2 release notes state that aircraft sinking on Forge was fixed.

The 1.3.0 -> 1.3.2 source range contains two commits named `fixed forge being forge`. The relevant
Bamboo Hopper change replaces direct access to the fluid-height field with the public
`getFluidHeight(FluidTags.WATER)` query when calculating gravity.

Observed repair shape:

```text
before:
  read internal fluid-height map directly

after:
  query water height through Entity API
```

Basis:

- symptom: AUTHOR_CLAIM from release changelog;
- repair diff: DIRECT_OBSERVATION of source commit;
- root cause: **UNKNOWN** beyond the narrow inference that direct internal fluid-height access was
  not portable/equivalent on the Forge path.

Reusable lesson:

> Cross-loader code should prefer the public environment query over loader-sensitive internal
> entity storage when physics depends on fluid contact.

Do not generalize this into "Forge fluid fields are always broken"; the evidence is this bounded
repair only.

## H2 — 1.3.3 public changelog and tagged-source delta disagree

Later cumulative public changelogs describe 1.3.3 as:

`Fixed rudder orientation`.

However:

- source tag `1.3.2+1.20.1` -> `ceef59afeff51645fc9ff852b77d56cdf48a372f`;
- source tag `1.3.3+1.20.1` -> `550b38d3dfdbf5cb6ec3f78468e0e60725a47605`;
- GitHub reports exactly one commit and one changed file between those tags;
- that diff restores only the protected static `ZERO_VEC4` field in `VehicleEntity`, with an
  addon-compatibility comment.

No model/resource change appears in the tag-to-tag diff.

Conclusion:

- release↔tag association is strong;
- exact distributed resource correspondence is **not proven**;
- do not cite the tag diff as proof of the public "rudder orientation" repair;
- raw JAR/resource comparison is the missing evidence.

This is precisely why Tech Hub separates source association from binary identity.

## H3 — addon compatibility restoration at the 1.3.3 tag head

The 1.3.3 tag-head commit message is `restored combat with addons`.

Its concrete source change reintroduces a protected static zero vector field to
`VehicleEntity`, explicitly noting that addons use it.

For Warfare Wings research this is directly relevant: the fixed-wing addon depends on Immersive
Aircraft implementation/API shape, not just documented public methods.

The exact downstream symbol that required the field was not established in this batch, so the
causal chain stops at the source-author statement plus repair diff.

Reusable lesson:

> When validating an addon against a pinned host MOD, preserve implementation-facing compatibility
> fields used by addons even if they look dead inside the host repository.

## H4 — `driftDrag` documentation/source contradiction

Issue #266 asks what aircraft datapack properties mean and includes `driftDrag`. A community reply
describes it as sideslip drag; the project owner later says the wiki was updated and clarifies the
decay fields.

But the exact 1.3.3 source examined here registers `friction`, not `driftDrag`, and
`VehicleData` reads registered stat names.

Therefore:

- the community explanation is a useful behavior hint;
- it is **not** implementation authority for the 1.3.3 ANCHOR;
- the source path indicates the JSON `driftDrag` field is not consumed as a VehicleStat in this
  release.

This contradiction matters because old Kneekura-bird theoretical code uses `driftDrag`.

Recommended verification if the raw 1.3.3 JAR is later locally available:

1. inspect/re-map `VehicleStat` and `VehicleData` from the distributed JAR;
2. run two otherwise identical datapacks differing only in `driftDrag`;
3. run another pair differing in `friction`;
4. compare fixed-input speed/turn telemetry.

Until then, source evidence is sufficient to reject `driftDrag` as a canonical 1.3.3 runtime
friction input in Tech Hub reasoning, while binary equivalence remains separately UNKNOWN.

## Remaining bounded history work

- capture the selected release pages / Issues / commit diffs into a Tech Hub profile so stable
  evidence IDs can be attached;
- compare the actual 1.3.2 and 1.3.3 Forge JAR resources if exact binary bytes become available;
- investigate only additional physics/network failures that become relevant to a concrete
  Kneekura-bird implementation decision.

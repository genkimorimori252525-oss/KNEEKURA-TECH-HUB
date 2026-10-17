# Full-state builder and dirty-mark callers — 2026-10-17

## Bounded question

Which exact-JAR Java call sites can request a full property snapshot or mark
player model state dirty? This inventory follows the
[property/reset lifecycle concern](PROPERTY-RESET-LIFECYCLE-RECOVERY-2026-10-17.md).
It does not execute networking, reproduce the concern or modify target behavior.

Artifact SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
All 955 classes were scanned. The three exact method targets are pinned in
`tools/full_sync_callers_ysm_265.py`: ModelInfoCapability.markDirty,
ModelInfoCapability.buildPacketForDispatch, and ServerDrivenPlayerPropertiesTracker.full.
Direct invokes and target MethodHandle arguments in BootstrapMethods are included.
External, native, reflective and dynamically generated calls remain outside scope.

## Results

10 direct call sites in 9 methods, plus one bootstrap target used by two
invokedynamic sites. The shared bootstrap is important: a plain invocation scan
would miss the two `cap::markDirty` fallback callbacks.

- Three direct buildPacketForDispatch calls all reside in CapabilityEvent:
  END-tick dirty callback (offset 79), entity-join callback (27), and tracking-start
  callback (18). The latter two pass false to the broadcast argument; dirty-tick
  passes true. They do not all imply the same audience or pending-state clearing.
- One direct tracker.full call is inside the model-ready builder lambda (84).
- Six direct markDirty calls: entity join without a channel/nonmandatory (15),
  setModelAndTexture (34), copyFrom (72), setSelectTexture (6), setDisabled (14),
  and setMandatory (14).
- CapabilityEvent bootstrap 18 targets markDirty and is used by entity-join
  invokedynamic 42 and tracking-start invokedynamic 33. Each supplies the absent
  branch of Optional.ifPresentOrElse when the full builder cannot find a model.

Role labels above are joined to the pinned comparison source at
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`, CapabilityEvent.java and
ModelInfoCapability.java, already captured by the SERVER-FULL-SYNC cohort.
setModelAndTexture returns if both strings already match; disabled/mandatory
only mark dirty when changed; setSelectTexture always marks dirty after storing.
The inventory includes complete caller bodies so these guards can be rechecked.

## What this resolves and what it does not

The scanned normal END-tick branch is change-driven: clean state uses the delta
tracker; full build is in the dirty branch. The direct-call inventory does not
show an unconditional periodic full resend, nor a full-builder call directly
from the client texture-ready method. This is not a universal absence proof:
a transitive setter, a later tracking event, external mod or native path may cause
another full snapshot. No runtime persistence duration or probability is claimed.

Consequently the delayed-reset concern remains conditional. It now has a bounded
Java producer/consumer/reset chain and explicit ordinary full-resend entry points.
A runtime observation is needed to resolve actual user-visible impact; do not
patch, weaken behavior or promote a mapping based solely on this candidate.

## Verification

The matching receipt passes 2 exact-inventory checks and rejects 6 corrupted
fixtures, including omission of the method-handle evidence. --capture regenerates
from --jar; normal verification takes --jar, --evidence and --out.
Independent semantic review NOT_RUN; central 669 mapping remains unchanged.
The fixed17 pipeline checkpoint is unchanged, not retroactively extended.

Continue independent Java input/query coverage while keeping this candidate
recorded for a separately authorized/available runtime reproduction.

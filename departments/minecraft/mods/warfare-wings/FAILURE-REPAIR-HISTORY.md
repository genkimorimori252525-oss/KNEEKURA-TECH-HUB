# Warfare Wings — Failure / Repair History

## Scope

Track: **ANCHOR — Minecraft 1.20.1 + Forge**

Pinned binary under study:

- supplied `warfare_wings-1.1.4-1.20.1-forge.jar`
- SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`

History window reviewed in this first pass: publicly visible Warfare Wings Forge 1.20.1 release
notes around versions 1.0.2 through 1.1.4, plus searches for an upstream source/issue tracker that
could provide repair diffs.

Status: **PARTIAL / discovery-only**.

The release-note pages were used as reconnaissance. They have not yet been captured into the
Tech Hub profile/CAS history adapter with immutable document IDs, and no upstream repair diff was
located in this pass. Therefore the observations below are **not imported failure-history cases**
and do not assert a root cause or verified repair.

## Discovery hints

### Machine-gun damage too low — public 1.0.2 Forge release note

The public 1.0.2 Forge changelog reports that machine-gun damage being too low was fixed.

Useful follow-up search surfaces:

- the weapon damage override / projectile damage path;
- Immersive Aircraft weapon API changes around the matching dependency version;
- any private/original source revision if it becomes available.

State: `DISCOVERED_NOT_CAPTURED`.

### Bomb power / Ju 87 mesh changes — public 1.0.2 Forge release note

The same release note reports a bomb-power change and a Ju 87 mesh correction.

These are separate symptoms and must not be combined into one causal case without source/diff
evidence.

State: `DISCOVERED_NOT_CAPTURED`.

### Machine guns unreliable in some multiplayer environments — public 1.1.2 Forge release note

The 1.1.2 Forge changelog reports that machine guns did not work properly in some multiplayer
environments.

This is especially relevant to the present architecture because the supplied static bytecode
delegates client fire messaging to Immersive Aircraft. However, that relationship does **not**
establish the historical root cause. A future case review should inspect the actual before/after
weapon/network code and exact Immersive Aircraft dependency versions.

State: `DISCOVERED_NOT_CAPTURED`.

### Missing IL-2 models / changed bullet model — public 1.1.2 Forge release note

The same release note reports missing IL-2 models and a changed bullet model.

These are asset/rendering history leads, not runtime proof for the supplied artifact.

State: `DISCOVERED_NOT_CAPTURED`.

### Client startup failure under some circumstances — public 1.1.4 Forge release note

The public 1.1.4 Forge file changelog says a client startup problem under some circumstances was
fixed.

The exact trigger, affected symbol and repair diff remain UNKNOWN in this batch.

State: `DISCOVERED_NOT_CAPTURED`.

## Upstream history limitation

No public source repository with a version-pinned Warfare Wings repair history was established in
this pass. Without Issue/PR/commit/diff evidence, the release-note statements remain author-facing
changelog claims only.

This is a legitimate partial result under
[FAILURE-REPAIR-HISTORY-v1.md](../../FAILURE-REPAIR-HISTORY-v1.md). It is intentionally not padded
with inferred causes.

## Next evidence needed

1. Capture the relevant release-note pages through the existing Tech Hub profile adapter so they
   receive immutable document/index IDs.
2. Locate the original Warfare Wings source/revision history if the author has published it, or
   record its continued unavailability.
3. For each retained case, inspect before/after code and the matching Immersive Aircraft dependency.
4. Only then author structured cases with separate symptom, trigger, root cause, repair and
   verification states.

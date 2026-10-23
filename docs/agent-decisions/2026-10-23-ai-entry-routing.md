# AI entry routing before historical search or runtime setup

Date: 2026-10-23 (Asia/Tokyo)
Scope: repository entry documentation; no runtime or product behavior changes.
Source baseline: `main` at `4866d7d7bbfe42a668437ebf38f8a13d6a3d59e7`.

## Problem and evidence

The root README already links the current Minecraft handoff. That handoff says it
is the first entry point for a fresh human or AI and supersedes older documents
that call themselves current. It identifies standalone KNEEKURA-LAB as historical
and distinguishes source discovery from runtime execution authority.

Entering through keyword-search results and an existing local Viewer instead of
the root README bypassed those instructions. The repository had no root AGENTS.md,
and an agent running in an external product checkout cannot automatically discover
instructions from a different repository. Adding more historical search matches
would not correct either entry problem.

## Decision and authorization

The project owner requested a cause analysis and a durable correction so AI agents
can reliably find and read the current guidance. Add a root AGENTS.md and a prominent
README link. Require the root README -> current department handoff -> relevant
subsystem order, current revision identity, and explicit runtime authority.

Add an external-product routing reminder in the affected product's own instructions.
Keep the prohibition on the old standalone / copied SimLab runtime in the product's
local continuity record. Do not publish private runtime records here.

## Alternatives and impact

Changing historical documents or deleting old sources would damage provenance and
would not ensure agents enter through current instructions. This change retains
those sources, adds routing at the automatically discovered repository boundary,
and explicitly covers agents working from another product repository.

No automatic experiment, service restart, migration, dependency, authority, or
canonical research claim is introduced. Current execution still requires its
existing registry, owner/session, disposable-world and runtime-attestation gates.

## Validation and recovery

Check new Markdown links against the current tracked tree, inspect the documentation
diff, and run git diff --check. No runtime is required for this documentation change.
Recovery is a normal revert of this documentation commit; historical evidence and
the owner's explicit runtime prohibition remain in force independently of the text.

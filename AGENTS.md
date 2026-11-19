# AI entry point

Read [AI-ENTRYPOINT.md](docs/AI-ENTRYPOINT.md) and [README.md](README.md) before
keyword search, implementation, or runtime setup. Resolve the registered local
Tech Hub checkout first when one is available: operational guides can exist there
without being tracked on GitHub. Search hits are supporting evidence, not a
replacement for this routing step.

## Minecraft / MOD-AI / Water Tank

1. Read `docs/PROJECT-GUIDE.md`, `docs/TANK-OPERATING-GUIDE.md`, and the relevant
   entries in `docs/AI-FEEDBACK.md` in the registered local checkout when present.
   Do not overwrite, commit wholesale, or execute from unrelated dirty work.
2. Resolve the current `main` revision and read the **Current Minecraft entry point**
   linked by the root README. At the time of this change, it is
   [CURRENT-HANDOFF-2026-10-02.md](departments/minecraft/CURRENT-HANDOFF-2026-10-02.md).
3. Read that handoff before the relevant subsystem instructions. It explicitly
   supersedes older documents that also call themselves "current". Follow newer
   entry-point links if the README changes; do not choose documents by filename alone.
   Local guides can route a capability to a separate reviewed feature worktree.
   Verify that worktree's actual source, revision, acceptance limits, and command
   help; `main` availability does not imply every guide-listed tool is installed.
4. For runtime work, inspect the current LAB / Debug Workspace and its documented
   registry, owner/session, disposable-world, and runtime-attestation requirements.
   Use the documented `task prepare` interface where applicable. Source discovery
   alone grants no execution authority.
5. Before launch, record the repository, resolved revision, selected subsystem,
   executable workspace, and applicable runtime authority. A listening local port
   or a directory named `KneekuraViewer` does not establish that it is the current
   supported Water Tank.

The canonical LAB source is `departments/minecraft/lab/` in this repository.
The former standalone `KNEEKURA-LAB` and the retained SimLab / Web Viewer code are
historical material. Do not start them as a fallback for current Water Tank work,
copy them into a new launcher, or treat their old `runSim` instructions as current.
Preserve history without promoting historical instructions into an active plan.

Keep UNKNOWN / PARTIAL / NOT_RUN outcomes explicit. A Viewer page or heartbeat is
not proof of current owner authority, loaded MOD identity, or native YSM rendering.

## External product repositories

An agent working outside this checkout will not automatically load this file.
When maintaining such a product's instructions, link its Tech Hub / Water Tank work
to this entry point and the root README, rather than to a historical LAB path.

## Data boundary

This repository is public. Keep worlds, generated runtime evidence, local config,
credentials, owner secrets, and private machine data out of commits and PR bodies.
Retain existing governance and runtime authority checks; these instructions do not
grant permission to bypass them or to restart a user-prohibited runtime.

# Persistent TechHub Tank host

2026-10-23 Asia/Tokyo. Decision and implementation plan; native acceptance remains NOT_RUN until receipts exist.

The user explicitly requests TechHub as parent, persistent reusable launch infrastructure, target MOD replacement, AI usability, stability and startup time comparable to the earlier run. This supersedes the Natural-owned runClient workaround in the preceding manual-adapter decision. NaturalGhast remains the first client, not the platform owner. Existing legacy LAB/SimLab/Web Viewer and rejected work/tank-lab remain prohibited.

## Design and alternatives

Adopt a minimal Forge host maintained inside TechHub, installed as a content-addressed persistent bundle under `%LOCALAPPDATA%/Kneekura/TechHub/Tank`. Keep dependencies and installed source outside temporary/artifact directories. Snapshot the canonical supervisor's JavaScript source closure and exact Java protocol helpers into the installation; removal of the development worktree must not break the installed launcher. Do not recreate the old Reimu host. Sharing Natural's runClient was smaller but couples every new MOD to that project; reusing a copied old host violates current constraints and retains hidden dependencies.

Initially support Minecraft 1.20.1, Forge 47.4.10, JDK17 and Gradle8.8, with an exact ForgeGradle version. Explicit profile entries distinguish mapped development JARs from Forge distribution JARs; distribution dependencies use ForgeGradle's documented `fg.deobf` coordinates. Other loaders/versions fail before launch. MOD dependencies are explicit, hashed inputs; incompatible MODs may still fail Forge's own dependency checks and are not automatically accepted.

Separate install/warm/prepare from start. Normal start is offline, never downloads or runs clean, and uses the warmed persistent host. Keep Gradle incremental state; measure launch-to-READY independently from installation, compilation and fixture preparation. Do not claim speed parity without comparable measured receipts.

AI entry points are doctor, install, warm, prepare, start, status, stop and evidence with structured results and explicit paths. Imports and preparation never launch. Profiles contain data, not executable shell fragments. Shared platform source cannot import Natural classes. Initial observation uses vanilla Projectile ownership, actual AttackEntityEvent, LivingHurtEvent and post-hurt state; target-specific semantics need a separate typed observer and are not inferred from generic events. Zero default captures and no input/mutation/motion grants.

Preserve canonical genuine native READY, exact Player/world/request/material/process bindings, finite windows, STOP identity, actual server/writer shutdown ACK and owned exit. Manual observation does not gain Arena/dispatcher authority. Do not relabel OBSERVE_GRID. Preserve all failed/interrupted trials. Original/finalized worlds are raw-read only; edit fresh private copies offline. The accepted Ghast swimming/product AI stays unchanged.

## Implementation and verification

- [ ] Add strict profile/install validation and tests for missing/tampered materials, wrong versions, path/reparse escapes, duplicate IDs, executable fields and non-launching prepare.
- [ ] Add pinned minimal host and immutable install with persistent caches, readiness metadata and exclusive lock against simultaneous shared-host builds/runs. Retain failures; never steal stale locks merely because time passed.
- [ ] Generalize the private native adapter and manifest; compile against current Forge classes, run Java/Node guards and original fixture assertions.
- [ ] Prepare Natural inputs independently, then use the same common launcher as another profile. Verify installed code still works without the source path; exercise a second profile without modifying the launcher.
- [ ] Run a short genuine native lifecycle, verifying READY/STOP/ACK/owned exit/original hashes. Only after that explicitly start the separate voluntary manual Rally window. Mark unexercised outcomes NOT_RUN.
- [ ] Update guides, feedback and CCG with actual results and limitations; record this scoped decision on the existing work branch. No merge or deployment is authorized.

Recovery: disable the new opt-in launcher, stop only its owned run, retain its immutable install and failed run evidence. Existing dispatcher/observer contracts and prior installations remain untouched. A missing cache is an actionable preparation error, never synthetic readiness.

Primary dependency reference: [ForgeGradle dependencies](https://docs.minecraftforge.net/en/fg-6.x/dependencies/).

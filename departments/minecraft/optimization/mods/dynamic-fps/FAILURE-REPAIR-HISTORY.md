# Dynamic FPS — bounded selected issue/fix history

Window: June 2024 config crash issue #204, Jan 2026 issues #283/#284; commit diffs for #204, #283 and a *separate* Forge mod detection repair reviewed. Whole histories, releases/JAR A/B and end-to-end captures **NOT_ACQUIRED**.

## DFPS-204 — unsupported Gson method in 1.20.1

[Issue #204](https://github.com/juliand665/Dynamic-FPS/issues/204) (2024-06-28) exact MC 1.20.1 **Fabric**, Dynamic FPS **3.5.0**, saving config crashes. [Patch `3bfa1b35747b5e41c9f68bf4a8b7709a53f26fca`](https://github.com/juliand665/Dynamic-FPS/commit/3bfa1b35747b5e41c9f68bf4a8b7709a53f26fca) parent `3d2cce71dc8999205df8ff241247a2e445f4d03a` in `Serialization.java` changes JsonObject.isEmpty() to JsonObject.size()==0, compatible with older Gson. Actual source diff observed, reporter runtime observation, *no own reproduction*. Relevant as dependency-version hazard, not as existing bug in the user's 3.11.4 release.

## DFPS-283 — optional graphics changes not fully reversible in newer 1.21.11

[Issue #283](https://github.com/juliand665/Dynamic-FPS/issues/283): minimal graphics settings reset upon leaving window in 1.21.11. [Commit `b7316de9b2d...`](https://github.com/juliand665/Dynamic-FPS/commit/b7316de9b2d9a6ed65d23ebbbebeefe4f21a07a9) parent `f9974058c361bafb22552cc8b2831e7982220f28` adds snapshot/restore fields for biome blend radius, cloud and weather range, cutout leaves, transparency. This is **newer 1.21.11 options API**, not a literal 1.20.1 code path; proposed acceptance must test effective graphics options in user's version.

## DFPS-284 — crash masking in another modpack, repair unpinned

[Issue #284](https://github.com/juliand665/Dynamic-FPS/issues/284): 1.21.1 NeoForge stack trace reported Dynamic FPS logging/initializing and distracting from another incompatible mod. Maintainer says 3.11.4 resolved it. **Exact repair diff is unverified for #284**; do not cite older [`2d7e8ba`](https://github.com/juliand665/Dynamic-FPS/commit/2d7e8ba5fd63d7a9f836e256dafe35a5de7aa290) ModList→LoadingModList change as a proven direct fix.

**Lesson:** render throttling changes event cadence and graphics config lifecycle; diagnostics must not hide the first actual failure. Runtime and benchmark NOT_RUN.

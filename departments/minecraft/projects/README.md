# KNEEKURA MOD product workspaces

Product-source workspaces are separate from the TECH-HUB `mods/` analysis catalog. Keeping a product in this monorepo does **not** merge Minecraft mod IDs, Forge artifacts, or runtime classpaths.

## Imported product

- [Kirby MOD](kirby-mod/README.md) — source, Forge build files, tests, GeckoLib geometry/animation, textures and audio imported from the owner's former private `Kirby_mod` repository.
- Source snapshot: `Kirby_mod@620226ee8a88351dd8918f73679977a15582337c`. The authoritative import is this TECH-HUB path after merge.
- Retain the original repository as read-only source-history / backup until the owner decides otherwise; do not make new feature changes in two repositories.

## Future sibling products

- `reimu-mod` — later integration, **not migrated by this Kirby import**.
- `NaturalGhastmod` — separate product, **not migrated by this Kirby import**.

These products should share a future [KNEEKURA MOD debug protocol](../design/2026-10-09-shared-mod-debug-roadmap.md) and appropriate TECH-HUB asset verification tools, but retain mod-specific gameplay semantics and independent registry IDs.

## Boundaries

- Do not merge unrelated mod jars into a single mod or rename `kirby_mod` just because the code lives in the same Git repository.
- TECH-HUB's existing `mod-ai/` and `lab/` are shared engineering services; do not duplicate them under each product.
- All development snapshots, test claims, and final artifacts must be bound to an exact TECH-HUB commit and a target product.
- Generated Gradle caches/builds and Minecraft user worlds are not product source.
